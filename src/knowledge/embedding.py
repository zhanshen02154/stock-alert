import logging
import os

from langchain_community.embeddings import DashScopeEmbeddings, OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class SafeDashScopeEmbeddings(DashScopeEmbeddings):
    """带空结果校验的 DashScope Embeddings 封装"""

    def embed_query(self, text: str) -> list[float]:
        result = super().embed_query(text)
        if not result:
            logger.error(f"DashScope embed_query 返回空结果, 输入文本: {text[:100]}")
            raise ValueError(f"Embedding 返回空结果，请检查 DASHSCOPE_API_KEY 是否正确设置。输入: {text[:100]}")
        return result


def get_qwen_emeddings() -> Embeddings:
    """
    获取嵌入模型
    :return:
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.warning("DASHSCOPE_API_KEY 环境变量未设置，Embedding 可能无法正常工作")

    return SafeDashScopeEmbeddings(
        dashscope_api_key=api_key,
        model="text-embedding-v4",
        max_retries=3,
    )