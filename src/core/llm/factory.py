"""LLM客户端工厂"""
from enum import Enum
from typing import Any, Optional

from .base import BaseLLMClient
from .providers import QwQClient, OpenAIClient


class LLMProvider(str, Enum):
    """支持的LLM提供商"""
    QWQ = "qwq"
    OPENAI = "openai"


class LLMClientFactory:
    """LLM客户端工厂类"""

    # 类注册表
    _class_registry: dict[str, type[BaseLLMClient]] = {
        LLMProvider.QWQ: QwQClient,
        LLMProvider.OPENAI: OpenAIClient,
    }
    # 实例缓存
    _instances: dict[str, BaseLLMClient] = {}

    @classmethod
    def register(cls, provider: str, client_class: type[BaseLLMClient]) -> None:
        """注册新的LLM提供商类"""
        cls._class_registry[provider] = client_class

    @classmethod
    def create(
        cls,
        provider: str | LLMProvider = LLMProvider.QWQ,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> BaseLLMClient:
        """创建LLM客户端实例"""
        provider_key = provider.value if isinstance(provider, LLMProvider) else provider

        if provider_key not in cls._class_registry:
            raise ValueError(f"不支持的LLM提供商: {provider}，支持的提供商: {list(cls._class_registry.keys())}")

        client_class = cls._class_registry[provider_key]
        return client_class(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )

    @classmethod
    def initialize(cls, config: dict[str, Any]) -> None:
        """初始化并缓存LLM客户端实例"""
        if "provider" not in config:
            raise ValueError("配置中缺少provider字段")
        
        provider_key = config["provider"]
        
        # 如果实例已存在，跳过
        if provider_key in cls._instances:
            return
        
        # 创建实例并缓存
        instance = cls.create(**config)
        cls._instances[provider_key] = instance

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> BaseLLMClient:
        """从配置字典创建客户端"""
        return cls.create(**config)

    @classmethod
    def get_instance(cls, provider: str | LLMProvider = LLMProvider.QWQ) -> BaseLLMClient:
        """获取已缓存的LLM客户端实例"""
        provider_key = provider.value if isinstance(provider, LLMProvider) else provider
        
        if provider_key not in cls._instances:
            raise ValueError(f"LLM客户端未初始化: {provider_key}，请先调用 initialize()")
        
        return cls._instances[provider_key]

    @classmethod
    def get_class(cls, provider: str | LLMProvider) -> type[BaseLLMClient]:
        """获取LLM客户端类（用于注册新提供商）"""
        provider_key = provider.value if isinstance(provider, LLMProvider) else provider
        return cls._class_registry[provider_key]

    @classmethod
    def clear(cls):
        cls._instances.clear()

