from functools import lru_cache

from langfuse import Langfuse
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from config.settings import get_app_config, get_langfuse_config


@lru_cache(maxsize=1)
def init_langfuse() -> None:
    """
    初始化langfuse
    :return:
    """
    app_env = get_app_config("environment")
    if app_env is None:
        app_env = "dev"
    langfuse_config = get_langfuse_config()
    langfuse_config["environment"] = app_env

    Langfuse(**langfuse_config)


def get_langfuse_client():
    """
    获取langfuse客户端
    :return:
    """
    return get_client()


def flush_langfuse():
    return get_langfuse_client().flush()


def get_callback_handler() -> CallbackHandler:
    return CallbackHandler()
