import json
import logging
from typing import Optional, List, Dict, Any

from src.storage.mysql import MySQLSessionStore

logger = logging.getLogger(__name__)


class SessionRepository:
    """会话仓库 - 同步实现"""

    def __init__(self, session_store: MySQLSessionStore):
        self.session_store = session_store

    def get_session_history(
            self,
            session_id: str,
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT id, session_id, role, content, metadata, created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                """
                params = [session_id]

                if limit:
                    sql += " LIMIT %s"
                    params.append(limit)

                cur.execute(sql, params)
                rows = cur.fetchall()
                return [
                    {
                        "id": row[0],
                        "role": row[2],
                        "content": row[3],
                        "metadata": json.loads(row[4]) if row[4] else {},
                        "created_at": row[5].isoformat()
                    }
                    for row in rows
                ]

    def save_message(
            self,
            session_id: str,
            role: str,
            content: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """保存消息"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, metadata)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, role, content, json.dumps(metadata or {}))
                )
                message_id = cur.lastrowid

                # 更新会话时间
                cur.execute(
                    "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (session_id,)
                )

        logger.debug(f"保存消息: session={session_id}, role={role}")
        return message_id

    def create_session(
            self,
            session_id: str,
            user_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建新会话"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, metadata)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, user_id or "anonymous", json.dumps(metadata or {}))
                )
        logger.debug(f"创建会话: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """删除会话及其消息"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE session_id = %s",
                    (session_id,)
                )
        logger.info(f"删除会话: {session_id}")

    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """更新会话的metadata"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET metadata = %s WHERE session_id = %s",
                    (json.dumps(metadata), session_id)
                )
        logger.debug(f"更新会话metadata: {session_id}")

    def get_user_sessions(
            self,
            user_id: str,
            limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        with self.session_store._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT `session_id`, `user_id`, `metadata`, `created_at`, `updated_at`
                    FROM `chat_sessions`
                    WHERE `user_id` = %s
                    ORDER BY `updated_at` DESC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                rows = cur.fetchall()
                result_list = []
                for row in rows:
                    result_list.append({
                        "session_id": row[0],
                        "user_id": row[1],
                        "metadata": json.loads(row[2]) if row[2] else {},
                        "created_at": row[3].isoformat(),
                        "updated_at": row[4].isoformat()
                    })
                return result_list

def create_session_repository(session_store: MySQLSessionStore) -> SessionRepository:
    return SessionRepository(session_store)
