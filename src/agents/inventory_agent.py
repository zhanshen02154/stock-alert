import logging
from typing import Optional, Dict, AsyncIterator, List, Any

import pymysql
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, ToolRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from src.agents.base_agent import BaseAgent
from src.core.llm import LLMClientFactory
from src.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class InventoryAgent(BaseAgent):
    """智能库存预警Agent"""

    system_msg: str = """
    你是一个库存助手，你需要推理，思考并选择相应的工具帮助用户解决库存的问题。
    """
    model: BaseChatModel | None = None
    config: Optional[Dict]
    sql_conn = None
    checkpointer = None
    _agent = None

    def __init__(self, agent_name: str, llm_config: Optional[Dict] = None):
        super().__init__(agent_name=agent_name, llm_config=llm_config)
        self.config = llm_config
        self._started = False
        self.tools = tool_registry.get_tools()

    def invoke(self, message: str, thread_id: str) -> List[dict[str, str]]:
        """
        同步调用Agent，返回最终结果
        
        Args:
            message: 用户输入消息
            thread_id: 线程ID，用于区分不同会话
            
        Returns:
            Agent的响应文本
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        result = self._agent.invoke({"messages": [{"role": "user", "content": message}]}, config)
        final_msg = result["messages"][-1]

        if hasattr(final_msg, "content") and final_msg.content:
            return [{"role": "assistant", "content": final_msg.content}]

        return [{"role": "assistant", "content": "执行错误"}]

    async def ainvoke(self, message: str, thread_id: str) -> List[dict[str, str]]:
        """
        异步请求
        :param message: 消息内容
        :param thread_id: 会话ID
        :return: 消息
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        result = await self._agent.ainvoke({"messages": [{"role": "user", "content": message}]}, config)
        final_msg = result["messages"][-1]
        if hasattr(final_msg, "content") and final_msg.content:
            return [{"role": "assistant", "content": final_msg.content}]

        return [{"role": "assistant", "content": "执行错误"}]

    def summary(self, message: str, thread_id: str, length: int = 30) -> str:
        """
        摘要
        :param length:
        :param thread_id:
        :param message: 消息内容
        :return: 摘要
        """
        template_str = """
        请总结以下内容并返回不超过{length}字的标题:
        {message}
        """
        prompt = PromptTemplate.from_template(template=template_str)
        prompt_msg = prompt.format(message=message, length=length)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        result = self._agent.invoke({"messages": [{"role": "user", "content": prompt_msg}]}, config=config)
        final_msg = result["messages"][-1]
        if hasattr(final_msg, "content") and final_msg.content:
            return str(final_msg.content)

        return "摘要错误"


    async def astream(self, message: str, thread_id: str = "1") -> AsyncIterator[str]:
        """
        流式调用Agent，逐步返回响应
        
        Args:
            message: 用户输入消息
            thread_id: 线程ID，用于区分不同会话
        Yields:
            Agent响应的文本片段
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        async for chunk in self._agent.astream({"messages": [{"role": "user", "content": message}]}, config):
            if "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if isinstance(msg, dict) and msg.get("content"):
                        yield msg["content"]
                    elif hasattr(msg, "content") and msg.content:
                        yield msg.content

    def start(self):
        if self._started:
            return
        self._started = True
        db_config = self.config.get("mysql", {})
        self.sql_conn = pymysql.connect(
            host=db_config.get("host", "127.0.0.1"),
            port=db_config.get("port", 3306),
            user=db_config.get("user", "local"),
            password=db_config.get("password", ""),
            database=db_config.get("database", ""),
            charset="utf8mb4",
            collation="utf8mb4_0900_ai_ci",
        )
        self.checkpointer = PyMySQLSaver(self.sql_conn)
        self.checkpointer.setup()
        self.model = LLMClientFactory.get_instance("qwq").client
        self._agent = create_agent(model=self.model, system_prompt=SystemMessage(content=self.system_msg),checkpointer=self.checkpointer,
                                   middleware=[
                                       SummarizationMiddleware(model=self.model,trigger=[("fraction", 0.8), ("tokens", 1024)], keep=["messages", 5]),
                                       ToolRetryMiddleware(
                                           max_retries=3,  # 最多重试 3 次
                                           backoff_factor=2.0,  # 指数回退乘数
                                           initial_delay=1.0,  # 从 1 秒延迟开始
                                           max_delay=20,  # 将延迟上限设置为 20 秒
                                           jitter=True,  # 添加随机抖动以避免“惊群”问题
                                           tools=self.tools
                                       ),
                                   ], tools=self.tools)

    def close(self):
        """关闭Agent，释放所有资源"""
        if not self._started:
            return
        self._started = False
        
        try:
            # 1. 先关闭工具资源（工具可能依赖数据库连接）
            if self._agent and hasattr(self._agent, 'tools'):
                for tool in self._agent.tools:
                    try:
                        if hasattr(tool, 'close'):
                            tool.close()
                            logger.info(f"Tool {tool.name} 已关闭")
                    except Exception as e:
                        logger.error(f"关闭工具 {getattr(tool, 'name', 'unknown')} 失败: {e}")
            
            # 2. 关闭数据库连接
            if self.sql_conn:
                try:
                    self.sql_conn.close()
                    logger.info("MySQL连接已关闭")
                except Exception as e:
                    logger.error(f"关闭MySQL连接失败: {e}")
            
            # 3. 清理引用
            self.checkpointer = None
            self._agent = None
            self.model = None
            logger.info("Agent已停止")
            
        except Exception as e:
            logger.error(f"关闭Agent时发生错误: {e}", exc_info=True)

def create_inventory_agent(config: Dict[str, Any]):
    """创建客户端"""
    return InventoryAgent(agent_name="inventory_agent", llm_config=config)