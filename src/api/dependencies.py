from functools import lru_cache
from typing import Any
from fastapi import Depends, Request
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from redis.asyncio import Redis
from config.settings import GLOBAL_CONFIG, get_agent_config
from src.agents.inventory_agent import InventoryAgent
from src.core.llm.llm import get_qwen_llm_client
from src.repository.session import SessionRepository
from src.repository.user import UserRepository
from src.service.chat import ChatService
from src.service.session import SessionService
from src.service.user import UserService


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


# 获取MySQL存储层 (从app.state)
def get_mysql_store_from_app(request: Request):
    if not request.app.state.mysql_store:
        raise RuntimeError("MySQL存储层未在应用启动时初始化")
    return request.app.state.mysql_store


@lru_cache(maxsize=1)
def get_session_repo(mysql_store = Depends(get_mysql_store_from_app)) -> SessionRepository:
    return SessionRepository(session_store=mysql_store)

def get_checkpointer(request: Request) -> BaseCheckpointSaver:
    """获取checkpointer (从app.state)"""
    if not hasattr(request.app.state, 'checkpointer') or request.app.state.checkpointer is None:
        raise RuntimeError("Checkpointer未在应用启动时初始化")
    return request.app.state.checkpointer


@lru_cache(maxsize=1)
def get_inventory_agent(
    request: Request,
    checkpointer: BaseCheckpointSaver = Depends(get_checkpointer),
) -> InventoryAgent:
    """
    获取库存Agent
    :param request:
    :param checkpointer: 检查点
    :return: InventoryAgent
    """
    conf = get_inventory_config()
    agent = InventoryAgent(agent_name="inventory", llm=request.app.state.qwen_llm, checkpointer=checkpointer, conf=conf)
    agent.start()
    return agent

@lru_cache(maxsize=1)
def get_user_repo(mysql_store = Depends(get_mysql_store_from_app)) -> UserRepository:
    return UserRepository(session_store=mysql_store)


@lru_cache(maxsize=1)
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    redis_client: Redis = Depends(get_redis_client_from_app)
) -> UserService:
    return UserService(user_repo=user_repo, redis_client=redis_client)


@lru_cache(maxsize=1)
def get_session_service(session_repo: SessionRepository = Depends(get_session_repo), agent: InventoryAgent = Depends(get_inventory_agent)) -> SessionService:
    return SessionService(session_repo=session_repo, agent=agent)


@lru_cache(maxsize=1)
def get_chat_service(session_repo: SessionRepository = Depends(get_session_repo), agent: InventoryAgent = Depends(get_inventory_agent)) -> ChatService:
    """获取聊天服务"""
    return ChatService(session_repo=session_repo, agent=agent)