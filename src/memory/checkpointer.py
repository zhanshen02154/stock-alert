import logging
from typing import Optional, Sequence

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver

from config.settings import get_checkpointer_config

logger = logging.getLogger(__name__)


class CheckpointerFactory:
    """
    检查点工厂类
    """

    _instance: (
        Optional[BaseCheckpointSaver]
        | Optional[MemorySaver]
        | Optional[AsyncRedisSaver]
    ) = None

    _config = {}

    @classmethod
    async def cleanup(cls):
        """
        关闭
        :return:
        """
        try:
            if cls._instance is not None:
                if isinstance(cls._instance, AsyncRedisSaver):
                    await cls._instance._redis.aclose(close_connection_pool=True)
                elif isinstance(cls._instance, MemorySaver):
                    cls._instance = None

            cls._instance = None
            logger.info("checkpointer cleanup finished")
        except Exception as e:
            logger.error(f"Failed to close checkpointer: {e}")

    @classmethod
    async def create_async_redis_saver(cls, **kwargs) -> AsyncRedisSaver:
        """
        创建异步redisSaver
        :return:
        """
        cls._instance = AsyncRedisSaver(
            redis_client=kwargs.get("redis_client"),
            ttl=cls._config.get(
                "ttl",
                {
                    "default_ttl": 604800,
                    "refresh_on_read": True,
                },
            ),
        )
        await cls._instance.setup()

        return cls._instance

    @classmethod
    async def start(cls, **kwargs) -> BaseCheckpointSaver:
        cls._config = get_checkpointer_config()
        if cls._instance is None:
            checkpointer_type = cls._config.get("type", "redis")
            if checkpointer_type == "redis":
                await cls.create_async_redis_saver(**kwargs)
            else:
                cls._instance = MemorySaver()

        return cls._instance

    @classmethod
    def get_instance(cls) -> BaseCheckpointSaver:
        return cls._instance

    @classmethod
    def has_checkpointer(cls) -> bool:
        """
        检查是否存在
        :return:
        """
        return cls._instance is not None

    @classmethod
    async def clear_checkpoint_by_thread_id(cls, thread_id: str):
        """
        删除指定会话的检查点
        :param thread_id: 会话ID/线程ID
        :return:
        """
        if not cls.has_checkpointer():
            raise ValueError("checkpointer is null")
        try:
            await cls._instance.adelete_thread(thread_id=thread_id)
        except Exception as e:
            raise e

    @classmethod
    async def remove_all_checkpointers(cls, thread_ids: Sequence[str]):
        if not cls.has_checkpointer():
            raise ValueError("checkpointer is null")
        await cls._instance.aprune(thread_ids=thread_ids, strategy="delete")
