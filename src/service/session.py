from typing import Any

from src.graph.inventory_manager import InventoryManagerGraph
from src.repository.session import SessionRepository


class SessionService:
    """会话管理服务层 - 同步实现"""

    def __init__(self, session_repo: SessionRepository, agent: InventoryManagerGraph):
        self.__session_repo = session_repo
        self.__agent = agent

    def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        return self.__session_repo.get_session_history(session_id)

    def save_message(
        self, session_id: str, role: str, content: str, metadata: dict[str, Any]
    ) -> int:
        return self.__session_repo.save_message(session_id, role, content, metadata)

    def create_session(
        self,
        session_id: str,
        user_id: str,
        title: str = "新对话",
        metadata: dict[str, Any] = None,
    ) -> dict[str, Any]:
        return self.__session_repo.create_session(
            session_id, user_id, title=title, metadata=metadata
        )

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

    async def update(self, session_id: str, user_id: int) -> str:
        """
        更新会话标题，自动通过summary生成总结标题

        Args:
            session_id: 会话ID
            user_id: 当前用户ID

        Returns:
            生成的标题

        Raises:
            ValueError: 会话不存在或不属于当前用户
        """
        # 检查会话是否存在且属于当前用户
        session = self.__session_repo.find_session_by_id(session_id, user_id)
        if not session:
            raise ValueError("会话不存在或无权限访问")

        if session.get("title") != "新对话":
            return session.get("title")

        # 获取会话历史消息，拼接为上下文
        history = self.__session_repo.get_session_history(session_id)
        message_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)

        # 调用agent.summary生成总结标题
        title = await self.__agent.summary(message_text)

        # 更新标题
        success = self.__session_repo.update_session_title(session_id, title)
        if not success:
            raise ValueError("更新会话标题失败")

        return title
