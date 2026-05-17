import logging
import os
import time
from typing import Any, Optional, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse.decorators import observe

from config.settings import get_llm_config
from src.core.llm.factory import create_llm_client
from src.graph.setup import GraphSetup, Context
from src.memory.checkpointer import CheckpointerFactory

logger = logging.getLogger(__name__)


class InventoryManagerGraph:
    """
    库存管理图
    """

    def __init__(
        self,
        debug=False,
        config: dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        self._debug = debug
        self._config = config
        self.callbacks = callbacks or []
        llm_kwargs = self._get_provider_kwargs(self._config["llm_provider"])
        self.openai_client = create_llm_client(
            model=llm_kwargs["model"],
            provider=self._config["llm_provider"],
            **llm_kwargs["params"],
        )
        worker_llm_config = get_llm_config("qwen")
        worker_llm_config["api_key"] = os.environ.get("DASHSCOPE_API_KEY")
        self._workerllm__client = create_llm_client(
            provider="qwen",
            base_url=os.environ.get("DASHSCOPE_API_BASE"),
            **worker_llm_config,
        )
        self.setup = self.setup_graph()

    def _get_provider_kwargs(self, provider: str) -> dict[str, Any]:
        """
        获取LLM供应商配置
        :return:
        """
        kwargs = get_llm_config(provider)
        if self.callbacks:
            kwargs["params"]["callbacks"] = self.callbacks

        return kwargs

    def setup_graph(self):
        """设置graph"""
        return GraphSetup(
            llm=self.openai_client.get_llm(),
            worker_llm=self._workerllm__client.get_llm(),
            conf=self._config,
        )

    @observe(capture_output=False)
    async def astream(self, message: str, thread_id: str, user_id: int):
        """
        异步流式传输
        :param message: 消息
        :param thread_id: 线程ID（可传入会话ID）
        :param user_id: 用户ID
        :return:
        """
        config: RunnableConfig = {
            "recursion_limit": 17,
            "configurable": {
                "thread_id": thread_id,
            },
        }
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        user_msg = f"""
请根据用户输入的内容完成回答
当前日期: {current_time}
用户输入: {message}
"""
        input_data = {
            "messages": ("user", user_msg),
            "user_input": message,
        }
        async for chunk in self.setup.workflow.astream(
            input_data,
            config=config,
            stream_mode="updates",
            context=Context(user_id=user_id),
        ):
            if isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        if messages and hasattr(messages[-1], "content"):
                            content = messages[-1].content
                            if content:
                                last_msg = messages[-1]
                                if hasattr(
                                    last_msg, "response_metadata"
                                ) and last_msg.response_metadata.get(
                                    "__is_handoff_back"
                                ):
                                    for msg in reversed(messages[:-1]):
                                        if hasattr(
                                            msg, "response_metadata"
                                        ) and msg.response_metadata.get(
                                            "__is_handoff_back"
                                        ):
                                            continue
                                        content = msg.content
                                        break
                                    else:
                                        continue
                                if isinstance(content, list):
                                    text_parts = []
                                    for block in content:
                                        if (
                                            isinstance(block, dict)
                                            and block.get("type") == "text"
                                        ):
                                            text_parts.append(block.get("text", ""))
                                    yield {"type": "text", "text": "".join(text_parts)}
                                else:
                                    yield {"type": "text", "text": content}

    async def aclose(self):
        """
        异步关闭
        :return:
        """
        if self._config:
            self._config.clear()
        self._config = None
        self.callbacks = None

        if self.setup:
            await self.setup.close()

        logger.info("AI代理已关闭")

    async def remove_session(self, session_id: str):
        """
        删除会话
        :param session_id: 会话ID
        :return:
        """
        try:
            await CheckpointerFactory.clear_checkpoint_by_thread_id(session_id)
        except Exception as e:
            logger.error(f"删除会话{session_id}失败: {e}")
            raise e

    async def summary(self, message: str) -> str:
        """
        总结首轮对话，生成标题
        :param message: 对话内容
        :return: 标题
        """
        sys_prompt = "请为以下对话内容生成不超过30字的标题，只输出标题本身，不要附加任何其他内容。"
        try:
            resp = await self._workerllm__client.get_llm().ainvoke(
                [
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content=message),
                ]
            )
            return resp.content
        except Exception as e:
            logger.error(f"生成总结标题失败: {e}")
            return "新对话"
