import logging
from typing import Any

from langchain_community.cache import AsyncRedisCache
from redis.asyncio import Redis

from config.settings import get_storage_config

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis缓存客户端"""

    __client: Redis | None = None
    __config: dict[str, Any] = {}

    def __init__(self, config: dict[str, Any]):
        self.__config = config

    async def conn(self):
        """连接"""
        try:
            if self.__client is None:
                password = self.__config.get("password", "")
                self.__client = Redis(
                    host=self.__config.get("host", "localhost"),
                    port=self.__config.get("port", 6379),
                    password=password,
                    db=self.__config.get("db", 0),
                    max_connections=self.__config.get("max_connections", 30),
                    health_check_interval=self.__config.get(
                        "health_check_interval", 15
                    ),
                    decode_responses=True,
                )
                if password:
                    await self.__client.auth(password=password)
                logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"连接Redis失败: {e}")
            raise e

    async def aclose(self):
        """异步关闭"""
        try:
            if self.__client:
                await self.__client.aclose()
                self.__client = None
                logger.info("Redis异步连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis失败: {e}")
            raise e

    def get_client(self):
        """获取客户端"""
        if self.__client is None:
            self.conn()
        return self.__client

    def ping(self):
        """
        检查连接
        :return:
        """
        return self.__client.ping()

    async def aget(self, key: str) -> str:
        """获取值"""
        return await self.__client.get(key)


def create_redis_client() -> RedisClient:
    """创建Redis客户端"""
    conf = get_storage_config("redis")
    return RedisClient(conf)


def create_async_redis_cache() -> AsyncRedisCache:
    conf = get_storage_config("redis")
    return AsyncRedisCache(
        redis_=Redis(
            host=conf.get("host", "localhost"),
            port=conf.get("port", 6379),
            password=conf.get("password", ""),
            db=conf.get("db", 0),
            max_connections=conf.get("max_connections", 30),
            health_check_interval=conf.get("health_check_interval", 15),
        )
    )
