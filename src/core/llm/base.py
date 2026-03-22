"""LLM客户端基类定义"""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Optional

from langchain_core.messages import BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel


class BaseLLMClient(ABC):
    """LLM客户端抽象基类"""

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.extra_params = kwargs
        self._client: Optional[BaseChatModel] = None

    @abstractmethod
    def _create_client(self) -> BaseChatModel:
        """创建底层LLM客户端"""
        pass

    @property
    def client(self) -> BaseChatModel:
        """懒加载获取客户端实例"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def invoke(self, messages: list[BaseMessage], **kwargs: Any) -> BaseMessage:
        """同步调用"""
        return self.client.invoke(messages, **kwargs)

    async def ainvoke(self, messages: list[BaseMessage], **kwargs: Any) -> BaseMessage:
        """异步调用"""
        return await self.client.ainvoke(messages, **kwargs)

    def stream(self, messages: list[BaseMessage], **kwargs: Any) -> Iterator[BaseMessage]:
        """流式输出"""
        yield from self.client.stream(messages, **kwargs)

    async def astream(self, messages: list[BaseMessage], **kwargs: Any) -> AsyncIterator[BaseMessage]:
        """异步流式输出"""
        async for chunk in self.client.astream(messages, **kwargs):
            yield chunk

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "BaseLLMClient":
        """绑定工具（支持Function Calling）"""
        self._client = self.client.bind_tools(tools, **kwargs)
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> "BaseLLMClient":
        """结构化输出"""
        self._client = self.client.with_structured_output(schema, **kwargs)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"
