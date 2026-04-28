import os

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings


def get_qwen_emeddings() -> Embeddings:
    """
    获取嵌入模型
    :return:
    """
    return DashScopeEmbeddings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        model="text-embedding-v4",
        max_retries=3,
    )
