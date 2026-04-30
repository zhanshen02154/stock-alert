import logging
from typing import Optional, Dict, List, Any, AsyncGenerator

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, ToolRetryMiddleware
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnablePassthrough, RunnableLambda
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver

# 导入工具模块，触发装饰器注册
import src.tools  # noqa: F401
from config.prompts.system import SYSTEM_PROMPTS
from src.agents.base_agent import BaseAgent
from src.knowledge.retriever import BaseKnowledgeRetriever
from src.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """智能库存预警Agent"""

    __system_prompt: str = ""
    __summary_prompt: str = ""
    __config: Optional[Dict]
    checkpointer: BaseCheckpointSaver | AsyncRedisSaver | None = None
    __agent = None
    __rag_chain = None

    def __init__(
        self,
        agent_name: str,
        conf: dict[str, Any],
        llm: BaseChatModel,
        checkpointer: BaseCheckpointSaver,
    ):
        super().__init__(agent_name=agent_name)
        self._started = False
        self.__config = conf
        self.llm = llm
        self.checkpointer = checkpointer
        self.__system_prompt = SYSTEM_PROMPTS.get("system_message")
        self.__summary_prompt = SYSTEM_PROMPTS.get("summary")

    async def rag_astream(self, message: str) -> AsyncGenerator[dict, None]:
        """
        RAG链式异步流式输出
        :param message: 用户消息
        :return: 流式生成 {"type": "text", "text": ...}
        """
        if not message or not message.strip():
            logger.warning("RAG查询消息为空，跳过检索")
            yield {"type": "text", "text": "请输入有效的查询内容"}
            return

        BaseKnowledgeRetriever.load_retriever()
        retriever = BaseKnowledgeRetriever.get_retriever(
            "smart_procurement_rules"
        )
        prompt = PromptTemplate.from_template(template=SYSTEM_PROMPTS.get("rag_system"))
        self.__rag_chain = (
            {
                "context": retriever | RunnableLambda(format_context),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        try:
            async for chunk in self.__rag_chain.astream(message):
                if chunk:
                    yield {"type": "text", "text": chunk}
        except Exception as e:
            logger.error(f"RAG流式输出异常: {e}")
            yield {"type": "text", "text": f"检索采购规则时发生错误：{e}"}

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
        result = self.__agent.invoke(
            {"messages": [HumanMessage(content=message)]}, config, config=config
        )
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
        result = await self.__agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}, config=config
        )
        final_msg = result["messages"][-1]
        if hasattr(final_msg, "content") and final_msg.content:
            return [{"role": "assistant", "content": final_msg.content}]
        return [{"role": "assistant", "content": "执行错误"}]

    async def astream(self, message: str, thread_id: str):
        """
        异步流式请求（Agent模式）
        :param message: 消息内容
        :param thread_id: 会话ID
        :return: 消息
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        async for chunk in self.__agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode="updates",
        ):
            for step, data in chunk.items():
                if step == "model":
                    last_message = data["messages"][-1]
                    # 处理文本内容
                    if hasattr(last_message, "content") and last_message.content:
                        yield {"type": "text", "text": f"{last_message.content}"}
                elif step == "tool_calls":
                    # 处理工具调用
                    for tool_call in data.get("messages", []):
                        if hasattr(tool_call, "name"):
                            yield {
                                "type": "tool_call",
                                "name": tool_call.name,
                                "text": f"调用工具: {tool_registry.get_name_by_tool(tool_call.name)}",
                            }

    async def summary(self, message: str) -> str:
        """总结首轮对话"""
        sys_prompt = "请为以下对话内容生成不超过30字的标题，只输出标题本身，不要附加任何其他内容。"
        try:
            resp = await self.llm.ainvoke(
                [
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content=message),
                ]
            )
            return resp.content
        except Exception as e:
            logger.error(f"生成总结标题失败: {e}")
            return "新对话"

    def start(self):
        """启动"""
        if self._started:
            return
        self._started = True
        self.tools = tool_registry.get_tools()
        self.__agent = create_agent(
            model=self.llm,
            system_prompt=SystemMessage(content=self.__system_prompt),
            checkpointer=self.checkpointer,
            middleware=[
                SummarizationMiddleware(
                    model=self.llm,
                    trigger=[("fraction", 0.8), ("tokens", 2048)],
                    keep=["messages", 5],
                    summary_prompt=self.__summary_prompt,
                ),
                ToolRetryMiddleware(
                    max_retries=3,  # 最多重试 3 次
                    backoff_factor=2.0,  # 指数回退乘数
                    initial_delay=1.0,  # 从 1 秒延迟开始
                    max_delay=30,  # 将延迟上限设置为 30 秒
                    jitter=True,  # 添加随机抖动以避免"惊群"问题
                    tools=self.tools,
                ),
            ],
            tools=self.tools,
        )

    async def close(self):
        """关闭Agent，释放所有资源"""
        if not self._started:
            return
        self._started = False
        self.__agent = None
        self.__rag_chain = None
        self.llm = None
        self.checkpointer = None
        self.tools = None
        logger.info("库存Agent已关闭")

    async def remove_session(self, session_id: str):
        """删除会话"""
        try:
            await self.checkpointer.adelete_thread(session_id)
        except Exception as e:
            logger.error(f"删除会话{session_id}失败: {e}")
            raise

    def healthz(self) -> bool:
        """健康检查"""
        return self._started


def format_context(documents: list[Document]) -> str:
    """
    将检索结果格式化为上下文字符串
    :param documents: 文档列表
    :return: 格式化后的上下文
    """
    if not documents:
        return ""

    context_parts = []
    for i, doc in enumerate(documents, 1):
        meta_info = ""
        if doc.metadata:
            title = doc.metadata.get("document_title", "")
            main = doc.metadata.get("main_title", "")
            secondary = doc.metadata.get("secondary_heading", "")
            headings = " > ".join(filter(None, [title, main, secondary]))
            if headings:
                meta_info = f"【{headings}】"

        context_parts.append(
            f"{meta_info}\n{doc.page_content}" if meta_info else doc.page_content
        )

    return "\n\n---\n\n".join(context_parts)
