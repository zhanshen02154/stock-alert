import logging
import os
import time
from typing import Any, Optional

from src.core.callbacks import get_callback_handlers
from src.core.middlewares import inject_system_prompt
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, ToolRetryMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from src import ToolRegistry
from src.core.llm.factory import create_llm_client
from src.core.prompts import get_prompt_manager
from src.core.schemas import AgentType, Context, InventoryResult
from src.knowledge.references import build_references
from src.memory.checkpointer import CheckpointerFactory

logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    库存智能助手
    """

    def __init__(self, conf: dict[str, Any]):
        self._conf = conf
        self._callbacks = get_callback_handlers()
        self._openai_client = self._create_openai_client_instance()
        self._checkpointer = CheckpointerFactory.get_instance()
        self._system_msg = self.__load_system_msg()
        self._agent = self.__load_agent()

    def _create_openai_client_instance(self):
        """
        创建大模型客户端
        """
        llm_conf = self._conf.get("model", {})
        provider = llm_conf.get("provider", "openai")
        return create_llm_client(
            model=llm_conf.get("name", "openai/gpt-5.4"),
            provider=provider,
            **llm_conf.get("params", {}),
        )

    def __load_system_msg(self):
        """
        加载智能体
        """
        env_flag: str = os.environ.get("ENV", "dev")
        return get_prompt_manager().get_prompt_template_by_label(
            name="supervisor/system", label=env_flag
        )

    def __load_agent(self):
        """
        加载智能体
        """
        env_flag: str = os.environ.get("ENV", "dev")
        tools = ToolRegistry.get_tools_by_group("tools_supply_chain")
        system_msg = get_prompt_manager().get_prompt_template_by_label(name="supervisor/system", label=env_flag)
        summary_prompt = get_prompt_manager().get_prompt_template_by_label(
            name="context_extraction_assistant", label=env_flag
        )
        return create_agent(
            name=AgentType.INVENTORY.value,
            context_schema=Context,
            checkpointer=self._checkpointer,
            model=self._openai_client.get_llm(),
            tools=tools,
            response_format=InventoryResult,
            system_prompt=system_msg.compile(),
            middleware=[
                inject_system_prompt,
                SummarizationMiddleware(
                    model=self._openai_client.get_llm(),
                    trigger=[("fraction", 0.8), ("tokens", 8192)],
                    keep=("messages", 5),
                    summary_prompt=summary_prompt.compile()
                ),
                ToolRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                    max_delay=30,
                    jitter=True,
                    tools=tools,
                ),
            ],
        )

    async def astream(self, message: str, thread_id: str, user_id: int):
        """
        异步流式请求（Agent模式）
        :param message: 消息内容
        :param thread_id: 会话ID
        :param user_id: 用户ID
        :return: 消息
        """
        config: RunnableConfig = {
            "configurable": {"thread_id": thread_id},
            "callbacks": self._callbacks,
            "metadata": {
                "langfuse_session_id": thread_id,
                "langfuse_user_id": user_id
            }
        }
        structured_response: Optional[InventoryResult] = None
        raw_chunks: list[dict[str, Any]] = []
        text_parts: list[str] = []

        async for chunk in self._agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            context=Context(user_id=user_id),
            stream_mode="updates",
        ):
            for step, data in chunk.items():
                if not isinstance(data, dict):
                    continue

                for item in data.get("messages") or []:
                    artifact = getattr(item, "artifact", None)
                    if isinstance(artifact, dict):
                        raw_chunks.extend(artifact.get("chunks", []))

                structured = data.get("structured_response")
                if structured is not None:
                    structured_response = structured

                # 结构化输出由模型以工具调用方式生成，不把该轮内容当正文输出
                if step != "model" or structured is not None:
                    continue

                messages = data.get("messages") or []
                if not messages:
                    continue

                last_message = messages[-1]
                if not isinstance(last_message, AIMessage):
                    continue

                text = self._extract_text(last_message.content)
                if text:
                    text_parts.append(text)
                    yield {"type": "text", "text": text}

        if structured_response is None:
            try:
                state = await self._agent.aget_state(config)
                structured_response = state.values.get("structured_response")
            except Exception as e:
                logger.error("获取结构化结果失败: %s", e)

        references = build_references(raw_chunks)
        if structured_response is None:
            structured_response = InventoryResult(
                summary="".join(text_parts).strip() or "未能生成结构化结果",
                reasoning="无",
                confidence=0.0,
                references=references,
                timestamp=int(time.time()),
            )
        else:
            structured_response.references = references

        yield {
            "type": "references",
            "items": [reference.model_dump() for reference in references],
        }
        yield {"type": "result", "data": structured_response.model_dump()}

    @staticmethod
    def _extract_text(content: Any) -> str:
        """
        提取模型输出的文本内容
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts)
        return ""

    async def aclose(self):
        """
        异步关闭
        """
        self._callbacks = []
        self._agent = None
        logger.info("库存智能助手已关闭")

    async def remove_session(self, session_id: str):
        """
        删除会话
        """
        await CheckpointerFactory.clear_checkpoint_by_thread_id(thread_id=session_id)

    async def summary(self, message: str) -> str:
        """
        总结首轮对话，生成标题
        """
        sys_prompt = "请为以下对话内容生成不超过30字的标题，只输出标题本身，不要附加任何其他内容。"
        try:
            resp = await self._openai_client.get_llm().ainvoke(
                [
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content=message),
                ]
            )
            return self._extract_text(resp.content).strip() or "新对话"
        except Exception as e:
            logger.error("生成总结标题失败: %s", e)
            return "新对话"
