import logging
from typing import Optional, Dict, List, Any
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, ToolRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver

# 导入工具模块，触发装饰器注册
import src.tools  # noqa: F401
from config.prompts.system import SYSTEM_PROMPTS
from src.agents.base_agent import BaseAgent
from src.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """智能库存预警Agent"""
    __system_prompt: str = ""
    __summary_prompt: str = ""
    __config: Optional[Dict]
    checkpointer: BaseCheckpointSaver | AsyncRedisSaver | None = None
    __agent = None

    def __init__(self, agent_name: str, conf: dict[str, Any], llm: BaseChatModel, checkpointer: BaseCheckpointSaver):
        super().__init__(agent_name=agent_name)
        self._started = False
        self.__config = conf
        self.__tools = tool_registry.get_tools()
        self.llm = llm
        self.checkpointer = checkpointer
        self.__system_prompt = SYSTEM_PROMPTS.get("system_message")
        self.__summary_prompt = SYSTEM_PROMPTS.get("summary")

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
        result = self.__agent.invoke({"messages": [{"role": "user", "content": message}]}, config)
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
        result = await self.__agent.ainvoke({"messages": [{"role": "user", "content": message}]}, config)
        final_msg = result["messages"][-1]
        if hasattr(final_msg, "content") and final_msg.content:
            return [{"role": "assistant", "content": final_msg.content}]
        return [{"role": "assistant", "content": "执行错误"}]

    def start(self):
        """启动"""
        if self._started:
            return
        self._started = True
        self.__agent = create_agent(model=self.llm, system_prompt=SystemMessage(content=self.__system_prompt, checkpointer=self.checkpointer),
                                    middleware=[
                                        SummarizationMiddleware(model=self.llm,
                                                                trigger=[("fraction", 0.8), ("tokens", 2048)],
                                                                keep=["messages", 10],
                                                                summary_prompt=self.__summary_prompt),
                                        ToolRetryMiddleware(
                                            max_retries=3,  # 最多重试 3 次
                                            backoff_factor=2.0,  # 指数回退乘数
                                            initial_delay=1.0,  # 从 1 秒延迟开始
                                            max_delay=30,  # 将延迟上限设置为 30 秒
                                            jitter=True,  # 添加随机抖动以避免“惊群”问题
                                            tools=self.__tools
                                        ),
                                    ], tools=self.__tools)

    async def close(self):
        """关闭Agent，释放所有资源"""
        if not self._started:
            return
        self._started = False
        self.__agent = None
        self.llm = None
        self.checkpointer = None

        if self.tools:
            for tool in self.tools:
                tool.close()
        self.tools = None
        logger.info("库存Agent已关闭")


    async def remove_session(self, session_id: str):
        """删除会话"""
        try:
            await self.checkpointer.adelete_thread(session_id)
        except Exception as e:
            raise e

    def healthz(self) -> bool:
        """健康检查"""
        return self._started
