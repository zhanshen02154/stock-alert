from typing import Any

from src.agents.inventory_agent import InventoryAgent
from src.repository.session import SessionRepository


class SessionService:
    """会话管理服务层 - 同步实现"""
    def __init__(self, session_repo: SessionRepository, agent: InventoryAgent):
        self.__session_repo = session_repo
        self.__agent = agent

    def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        return self.__session_repo.get_session_history(session_id)

    def save_message(self, session_id: str, role: str, content: str, metadata: dict[str, Any]) -> int:
        return self.__session_repo.save_message(session_id, role, content, metadata)

    def create_session(self, session_id: str, user_id: str, title: str = "新对话", metadata: dict[str, Any] = None) -> dict[str, Any]:
        return self.__session_repo.create_session(session_id, user_id, title=title, metadata=metadata)

    async def delete_session(self, session_id: str) -> None:
        try:
            self.__session_repo.delete_session(session_id=session_id)
            await self.__agent.remove_session(session_id=session_id)
        except Exception as e:
            raise e

    def update_session_metadata(self, session_id: str, metadata: dict[str, Any]):
        return self.__session_repo.update_session_metadata(session_id, metadata)

    def get_user_sessions(self, user_id: int, limit: int = 10):
        return self.__session_repo.get_user_sessions(user_id=user_id, limit=limit)