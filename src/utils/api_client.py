import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    """API客户端"""

    __sync_client: Optional[httpx.Client] = None
    __async_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_sync_client(cls) -> httpx.Client:
        """获取同步HTTP客户端（单例模式）"""
        if cls.__sync_client is None:
            cls.__sync_client = httpx.Client(
                timeout=8,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return cls.__sync_client

    @classmethod
    def get_async_client(cls) -> httpx.AsyncClient:
        """获取异步HTTP客户端（单例模式）"""
        if cls.__async_client is None:
            cls.__async_client = httpx.AsyncClient(
                timeout=8,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return cls.__async_client

    @classmethod
    async def close_all(cls):
        """关闭所有客户端连接"""
        if cls.__sync_client:
            cls.__sync_client.close()
            cls.__sync_client = None
        if cls.__async_client:
            await cls.__async_client.aclose()
            cls.__async_client = None

        logger.info("HTTP客户端已关闭")
