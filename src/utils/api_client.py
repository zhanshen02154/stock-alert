from typing import Optional
import httpx


class ApiClient:
    """API客户端管理器"""
    def __init__(self):
        self.__sync_client: Optional[httpx.Client] = None
        self.__async_client: Optional[httpx.AsyncClient] = None

    def get_sync_client(self) -> httpx.Client:
        """获取同步HTTP客户端（单例模式）"""
        if self.__sync_client is None:
            self.__sync_client = httpx.Client(
                timeout=8,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self.__sync_client

    def get_async_client(self) -> httpx.AsyncClient:
        """获取异步HTTP客户端（单例模式）"""
        if self.__async_client is None:
            self.__async_client = httpx.AsyncClient(
                timeout=8,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self.__async_client

    async def close_all(self):
        """关闭所有客户端连接"""
        if self.__sync_client:
            self.__sync_client.close()
            self.__sync_client = None
        if self.__async_client:
            await self.__async_client.aclose()
            self.__async_client = None

ApiClientManager = ApiClient()
