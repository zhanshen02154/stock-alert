import logging
from typing import Any

from langchain_core.vectorstores import VectorStoreRetriever
from pymilvus import Function, FunctionType

from src.knowledge import vector_store

logger = logging.getLogger(__name__)


def _default_rrf_reranker(k: int = 60) -> Function:
    """创建默认的 RRF 重排序器"""
    return Function(
        name="rrf",
        input_field_names=[],
        function_type=FunctionType.RERANK,
        params={"reranker": "rrf", "k": k},
    )


class BaseKnowledgeRetriever:
    """通用的检索器逻辑封装"""

    __retrievers: dict[str, VectorStoreRetriever] = {}

    @classmethod
    def get_retriever(
        cls,
        collection_name: str,
        **kwargs,
    ) -> Any:
        """
        工厂方法：根据集合名动态生成检索器
        对于多向量字段集合（如 dense + BM25），会自动走混合搜索，
        通过 search_kwargs 传递 reranker 和 fetch_k。

        :param collection_name: 集合名称
        """
        if not vector_store.milvus_manager:
            raise Exception("Milvus 管理器未初始化")

        if collection_name not in cls.__retrievers:
            cls.__retrievers[collection_name] = (
                vector_store.milvus_manager.get_collection(
                    collection_name=collection_name
                ).as_retriever(**kwargs)
            )

        return cls.__retrievers[collection_name]

    @classmethod
    def load_retriever(cls):
        if "smart_procurement_rules" in cls.__retrievers:
            return cls
        cls.__retrievers["smart_procurement_rules"] = (
            vector_store.milvus_manager.get_collection(
                collection_name="smart_procurement_rules"
            ).as_retriever(
                search_kwargs={"k": 4, "reranker": _default_rrf_reranker(60)}
            )
        )

        return cls

    @classmethod
    def close(cls):
        if not cls.__retrievers:
            return

        cls.__retrievers.clear()
