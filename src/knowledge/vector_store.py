import logging
from typing import Any, Optional, List

from pymilvus import connections, MilvusClient, AnnSearchRequest
from pymilvus.milvus_client import IndexParams

from config.settings import get_storage_config
from src.knowledge.embedding import get_qwen_emeddings

logger = logging.getLogger(__name__)


class MilvusManager:
    def __init__(self, connection_args: dict[str, Any]):
        self._embeddings = get_qwen_emeddings()
        self.__connection_args = connection_args
        self.__alias = "default"
        self.__client = MilvusClient(
            uri=self.__connection_args["uri"],
            alias=self.__alias,
            db_name="default",
            timeout=10,
        )

    def connect(self):
        """
        连接到数据库
        :return:
        """
        connections.connect(
            alias=self.__alias,
            user=self.__connection_args["user"],
            password=self.__connection_args["password"],
            host=self.__connection_args["host"],
            port=self.__connection_args["port"],
            db_name=self.__connection_args["db_name"],
        )
        self.__client.load_collection(collection_name="smart_procurement_rules")

    def create_index(
        self,
        collection_name: str,
        index_params: IndexParams,
        timeout: Optional[float] = 8,
        **kwargs,
    ):
        """
        创建索引
        :param collection_name: 集合名称
        :param index_params: 索引参数
        :param timeout: 超时时间
        :param kwargs: 其他参数（和client.create_index参数类似）
        :return:
        """
        try:
            self.__client.create_index(
                collection_name=collection_name,
                index_params=index_params,
                timeout=timeout,
                **kwargs,
            )
        except Exception as e:
            logger.error(e, exc_info=e)

    def hybrid_search(
        self,
        collection_name: str,
        ann_requests: List[AnnSearchRequest],
        search_kwargs: dict[str, Any],
        k: int = 4,
        timout: Optional[float] = 8.0,
    ) -> list[Any] | list[list[dict]]:
        """
        混合搜索 - 使用 AnnRequest 构造查询
        :param timout: 超时时间
        :param ann_requests:
        :param collection_name: 集合名称
        :param k: 返回结果数量，默认3
        :param search_kwargs: 其他参数
        :return: 搜索结果列表
        """
        try:
            # 执行混合搜索
            results = self.__client.hybrid_search(
                reqs=ann_requests,
                collection_name=collection_name,
                limit=k,
                output_fields=["text", "chapter_path", "document_title"],
                timeout=timout,
                **search_kwargs,
            )

            return results

        except Exception as e:
            logger.error(f"混合搜索失败: {e}", exc_info=e)
            return []

    def close(self):
        """关闭所有缓存的 Milvus 实例"""
        self.__client.close()
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
            "host": conf.get("host", "127.0.0.1"),
            "port": conf.get("port", 19530),
            "user": conf.get("user", "testuser"),
            "password": conf.get("password", ""),
        }
    )
    milvus_manager.connect()
    logger.info("Milvus管理器加载完成")


async def close_milvus_manager():
    """
    关闭milvus管理器
    :return:
    """
    global milvus_manager
    if milvus_manager is not None:
        milvus_manager.close()
        milvus_manager = None

        logger.info("Milvus管理器已关闭")


def get_milvus_manager():
    global milvus_manager
    if milvus_manager is None:
        return None
    return milvus_manager
