import logging
from typing import Any, Optional

from langchain_milvus import Milvus, BM25BuiltInFunction
from pymilvus.milvus_client import IndexParams

from config.settings import get_storage_config
from src.knowledge.embedding import get_qwen_emeddings

logger = logging.getLogger(__name__)


class MilvusManager:
    def __init__(self, connection_args: dict[str, Any]):
        self.embeddings = get_qwen_emeddings()
        self.connection_args = connection_args
        # 缓存实例：{collection_name: Milvus_Object}
        self._instances: dict[str, Milvus] = {}

    def get_collection(
        self,
        collection_name: str,
    ) -> Milvus:
        """获取或创建 Collection 实例
        :param collection_name: 集合名称
        """
        if collection_name not in self._instances:
            self._instances[collection_name] = Milvus(
                embedding_function=self.embeddings,
                collection_name=collection_name,
                connection_args=self.connection_args,
                index_params=[
                    {
                        "metric_type": "COSINE",  # 余弦相似度，适合文本语义
                        "index_type": "HNSW",  # 高性能图索引，召回率高
                        "params": {
                            "M": 16,  # 每个节点的连接数，影响召回率（越大越好，但内存消耗大）
                            "efConstruction": 256,  # 构建时的搜索范围，影响构建质量
                        },
                    },
                    {
                        "metric_type": "BM25",
                        "index_type": "AUTOINDEX",
                    },
                ],
                vector_field=["dense_vector", "sparse_vector"],
                builtin_function=BM25BuiltInFunction(
                    input_field_names="text", output_field_names="sparse_vector"
                ),
                drop_old=False,
                auto_id=True,
                consistency_level="Bounded",
                timeout=30,
            )

        return self._instances[collection_name]

    def create_index(
        self,
        collection_name: str,
        index_params: IndexParams,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> None:
        if collection_name not in self._instances:
            raise ValueError(f"Collection {collection_name} not found")
        return self._instances[collection_name].client.create_index(
            collection_name=collection_name,
            index_params=index_params,
            timeout=timeout,
            **kwargs,
        )

    async def aclose(self):
        """关闭所有缓存的 Milvus 实例"""
        if self._instances:
            for k in self._instances:
                instance = self._instances[k]
                instance.client.close()
                if instance.aclient is not None:
                    await instance.aclient.close()
        self._instances.clear()
        logger.info("Milvus管理器已关闭")


milvus_manager: MilvusManager | None = None


def load_milvus_manager():
    """
    加载Milvus管理器
    :return:
    """
    conf = get_storage_config("milvus")
    global milvus_manager
    milvus_manager = MilvusManager(
        connection_args={
            "uri": f"http://{conf.get('host', '127.0.0.1')}:{conf.get('port', 19530)}",
            "token": f"{conf.get("user")}:{conf.get('password')}",
            "db_name": conf.get("db_name", "inventory"),
        }
    )
    logger.info("Milvus管理器加载完成")


async def close_milvus_manager():
    """
    关闭milvus管理器
    :return:
    """
    global milvus_manager
    if milvus_manager is not None:
        await milvus_manager.aclose()
        milvus_manager = None

        logger.info("Milvus管理器已关闭")
