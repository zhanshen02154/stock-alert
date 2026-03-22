"""
LLM客户端统一入口

使用示例:
    # 方式1：工厂方法创建
    from src.core.llm_client import create_llm_client

    client = create_llm_client(provider="qwq", model_name="qwen-plus")

    # 方式2：直接使用工厂类
    from src.core.llm_client import LLMClientFactory, LLMProvider

    client = LLMClientFactory.create(
        provider=LLMProvider.QWQ,
        model_name="qwen-plus",
        temperature=0.7
    )

    # 方式3：从配置创建
    config = {"provider": "openai", "model_name": "gpt-4o"}
    client = LLMClientFactory.from_config(config)

    # 调用
    from langchain_core.messages import HumanMessage

    response = client.invoke([HumanMessage(content="你好")])
    print(response.content)

    # 流式输出
    for chunk in client.stream([HumanMessage(content="讲个故事")]):
        print(chunk.content, end="", flush=True)
"""

from .llm import BaseLLMClient, LLMClientFactory, LLMProvider
from .llm.factory import LLMClientFactory as _LLMClientFactory

def create_llm_client(
    provider: str | LLMProvider = LLMProvider.QWQ,
    model_name: str | None = None,
    **kwargs
) -> BaseLLMClient:
    """便捷函数：创建LLM客户端"""
    return _LLMClientFactory.create(provider=provider, model_name=model_name, **kwargs)


__all__ = [
    "BaseLLMClient",
    "LLMClientFactory",
    "LLMProvider",
    "create_llm_client",
]
