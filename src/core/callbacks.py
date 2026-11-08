import os

from langchain_core.callbacks import BaseCallbackHandler
from langfuse.langchain import CallbackHandler


def get_callback_handlers() -> list[BaseCallbackHandler]:
    """
    获取回调处理器列表
    """
    return [
        CallbackHandler(public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"))
    ]