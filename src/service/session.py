from typing import Any

from src.repository.session import SessionRepository


class SessionService:
    """会话管理服务层 - 同步实现"""
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        return self.session_repo.get_session_history(session_id)

    def save_message(self, session_id: str, role: str, content: str, metadata: dict[str, Any]) -> int:
        return self.session_repo.save_message(session_id, role, content, metadata)

    def create_session(self, session_id: str, user_id: str, metadata: dict[str, Any]) -> None:
        return self.session_repo.create_session(session_id, user_id, metadata=metadata)

    def delete_session(self, session_id: str) -> None:
        return self.session_repo.delete_session(session_id=session_id)

    def update_session_metadata(self, session_id: str, metadata: dict[str, Any]):
        return self.session_repo.update_session_metadata(session_id, metadata)

    def get_user_sessions(self, user_id: str, limit: int = 10):
        return self.session_repo.get_user_sessions(user_id=user_id, limit=limit)


def create_session_service(session_repo: SessionRepository) -> SessionService:
    return SessionService(session_repo=session_repo)
