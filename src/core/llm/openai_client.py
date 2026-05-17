import os
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_qwq import ChatQwen, ChatQwQ

from src.core.llm.base_client import BaseLLMClient
from src.core.llm.validators import validate_model

# Kwargs forwarded from user config to ChatOpenAI
_PASSTHROUGH_KWARGS = (
    "timeout",
    "max_retries",
    "reasoning_effort",
    "api_key",
    "callbacks",
    "http_client",
    "http_async_client",
    "temperature",
    "max_tokens",
    "streaming",
)

# Provider base URLs and API key env vars
_PROVIDER_CONFIG = {
    "qwen": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_API_KEY",
    ),
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "openai": ("https://api.ofox.ai/v1", "OPENAI_API_KEY"),
}


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> BaseChatModel:
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.provider in _PROVIDER_CONFIG:
            default_base, api_key_env = _PROVIDER_CONFIG[self.provider]
            llm_kwargs["base_url"] = self.base_url or default_base
            if "api_key" not in self.kwargs:
                llm_kwargs["api_key"] = os.environ.get(api_key_env)
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        # Forward user-provided kwargs
        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        if self.provider == "openai":
            llm_kwargs["use_responses_api"] = True

        if (
            llm_kwargs["model"] == "qwen3.6-plus"
            or llm_kwargs["model"] == "qwen3.5-plus"
            or llm_kwargs["model"] == "qwen3.5-plus-2026-04-20"
            or llm_kwargs["model"] == "qwen3-14b"
            or llm_kwargs["model"] == "qwen3.5-plus-2026-02-15"
        ):
            return ChatQwen(**llm_kwargs)
        elif llm_kwargs["model"] == "qwq-plus":
            return ChatQwQ(**llm_kwargs)

        return ChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """
        验证model是否支持
        :return:
        """
        return validate_model(self.model, self.provider)
