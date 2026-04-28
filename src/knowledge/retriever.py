import logging

from langchain_core.vectorstores import VectorStoreRetriever

from src.knowledge import vector_store

logger = logging.getLogger(__name__)


class BaseKnowledgeRetriever:
    """通用的检索器逻辑封装"""

    @staticmethod
    def get_retriever(collection_name: str, **kwargs) -> VectorStoreRetriever:
        """工厂方法：根据集合名动态生成检索器"""
        if not vector_store.milvus_manager:
            raise Exception("Milvus 管理器未初始化")
        return vector_store.milvus_manager.get_collection(collection_name).as_retriever(
            **kwargs
        )

    @staticmethod
    def get_collection(collection_name: str):
        """
        获取集合
        :param collection_name: 集合名
        :return:
        """
        return vector_store.milvus_manager.get_collection(collection_name)
