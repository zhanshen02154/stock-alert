import logging
from typing import Any

from langchain_milvus import Milvus

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
                auto_id=True,
                drop_old=False,
                timeout=30,
            )
        return self._instances[collection_name]

    def close(self):
        """关闭所有缓存的 Milvus 实例"""
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


def close_milvus_manager():
    """
    关闭milvus管理器
    :return:
    """
    global milvus_manager
    if milvus_manager:
        milvus_manager.close()
        milvus_manager = None
