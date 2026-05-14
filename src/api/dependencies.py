from functools import lru_cache
from typing import Any

from fastapi import Depends, Request
from langgraph.checkpoint.base import BaseCheckpointSaver
from redis.asyncio import Redis

from config.settings import GLOBAL_CONFIG, get_agent_config
from src.graph.inventory_manager import InventoryManagerGraph
from src.knowledge.vector_store import MilvusManager
from src.repository.session import SessionRepository
from src.repository.user import UserRepository
from src.service.chat import ChatService
from src.service.session import SessionService
from src.service.user import UserService
from src.storage.mysql import get_mysql_session_store


def get_system_config():
    return GLOBAL_CONFIG


def get_inventory_config() -> dict[str, Any]:
    """获取库存Agent配置"""
    return get_agent_config("inventory")


# 获取Redis客户端 (从app.state)
def get_redis_client_from_app(request: Request) -> Redis:
    client = request.app.state.redis_client.get_client()
    if not client:
        raise RuntimeError("Redis客户端未在应用启动时初始化")
    return client


# 获取MySQL存储层 (从全局变量)
def get_mysql_store_from_global():
    return get_mysql_session_store()


@lru_cache(maxsize=1)
def get_session_repo(
    mysql_store=Depends(get_mysql_store_from_global),
) -> SessionRepository:
    return SessionRepository(session_store=mysql_store)


def get_checkpointer(request: Request) -> BaseCheckpointSaver:
    """获取checkpointer (从app.state)"""
    if (
        not hasattr(request.app.state, "checkpointer")
        or request.app.state.checkpointer is None
    ):
        raise RuntimeError("Checkpointer未在应用启动时初始化")
    return request.app.state.checkpointer


def get_inventory_graph(request: Request) -> InventoryManagerGraph:
    """获取库存图 (从app.state)"""
    if not hasattr(request.app.state, "inventory_graph"):
        raise RuntimeError("InventoryManagerGraph未在应用启动时初始化")
    return request.app.state.inventory_graph


@lru_cache(maxsize=1)
def get_user_repo(mysql_store=Depends(get_mysql_store_from_global)) -> UserRepository:
    return UserRepository(session_store=mysql_store)


@lru_cache(maxsize=1)
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    redis_client: Redis = Depends(get_redis_client_from_app),
) -> UserService:
    return UserService(user_repo=user_repo, redis_client=redis_client)


@lru_cache(maxsize=1)
def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repo),
    agent: InventoryManagerGraph = Depends(get_inventory_graph),
) -> SessionService:
    return SessionService(session_repo=session_repo, agent=agent)


@lru_cache(maxsize=1)
def get_milvus_manager(req: Request) -> MilvusManager:
    return req.state.vector_store


@lru_cache(maxsize=1)
def get_chat_service(
    session_repo: SessionRepository = Depends(get_session_repo),
    agent: InventoryManagerGraph = Depends(get_inventory_graph),
) -> ChatService:
    """获取聊天服务"""
    return ChatService(session_repo=session_repo, agent=agent)
