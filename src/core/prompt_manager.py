from typing import Optional

from langfuse.model import TextPromptClient, ChatPromptClient

from config.settings import get_prompt_manager_config
from src.core.tracer import get_langfuse_client


class PromptManager:
    """
    提示词管理器
    """

    def __init__(
        self,
        driver: str = "langfuse",
        cache_ttl_seconds: int = 600,
    ) -> None:
        self.__driver = driver
        self.__cache_ttl_seconds = cache_ttl_seconds

    def get_prompt(
        self,
        name: str,
        label: str = "dev",
        version: Optional[str] = None,
        prompt_type="text",
    ) -> TextPromptClient | ChatPromptClient:
        prompt = get_langfuse_client().get_prompt(
            name=name,
            label=label,
            type=prompt_type,
            version=version,
            cache_ttl_seconds=self.__cache_ttl_seconds,
        )

        return prompt

    def get_prompt_by_environment(
        self, name: str, label: str = "dev", prompt_type="text"
    ) -> TextPromptClient | ChatPromptClient:
        """
        获取指定环境的提示词
        :param label: 环境
        :param name: 名称
        :param prompt_type: 提示词类型
        :return:
        """
        return get_langfuse_client().get_prompt(
            name=name,
            type=prompt_type,
            cache_ttl_seconds=self.__cache_ttl_seconds,
            label=label,
        )

    def compile_prompt(
        self,
        name: str,
        variables: dict,
        label: str = "dev",
        version: Optional[str] = None,
    ) -> str:
        """
        编译提示词
        :param name: 提示词名称
        :param variables: 变量及赋值
        :param version: 版本
        :param label: 标签
        :return:
        """
        prompt = self.get_prompt(name, label, version)
        return prompt.compile(**(variables or {}))


prompt_manager: PromptManager | None = None


def create_prompt_manager():
    """
    创建提示词管理器
    :return:
    """
    global prompt_manager
    if prompt_manager is None:
        config = get_prompt_manager_config()
        cache_ttl_seconds = config.get("prompt_cache_ttl", 600)
        driver = config.get("driver", "langfuse")
        prompt_manager = PromptManager(
            driver=driver, cache_ttl_seconds=cache_ttl_seconds
        )


def get_prompt_manager() -> PromptManager:
    """
    获取提示词管理器实例（运行时读取，避免 import 时绑定到 None）
    :return: PromptManager 实例
    """
    if prompt_manager is None:
        raise RuntimeError(
            "PromptManager 未初始化，请先在应用启动时调用 create_prompt_manager()"
        )
    return prompt_manager
