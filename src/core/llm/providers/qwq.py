"""通义千问(QwQ) LLM客户端"""
import os
from typing import Any, Optional

from ..base import BaseLLMClient
from langchain_qwq import ChatQwen


class QwQClient(BaseLLMClient):
    """通义千问客户端（使用langchain-qwq）"""

    def __init__(
        self,
        model_name: str = "qwen-plus",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ):
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        base_url = base_url or os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        super().__init__(model_name, api_key, base_url, temperature, **kwargs)

    def _create_client(self):
        return ChatQwen(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            **self.extra_params
        )
