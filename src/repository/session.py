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
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT id, session_id, role, content, created_at
                    FROM `chat_messages`
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
                        "created_at": row[4].timestamp() * 1000
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
        with self.session_store.get_connection() as conn:
            conn.begin()
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

            conn.commit()
        return message_id

    def create_session(
            self,
            session_id: str,
            user_id: Optional[str] = None,
            title: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建新会话，返回会话信息"""
        with self.session_store.get_connection() as conn:
            conn.begin()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, title, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, user_id or -1, title or "新对话", json.dumps(metadata or {}))
                )

                conn.commit()

                # 查询刚创建的会话信息
                cur.execute(
                    """
                    SELECT session_id, title, created_at, updated_at
                    FROM chat_sessions
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                row = cur.fetchone()
        logger.debug(f"创建会话: {session_id}")
        return {
            "id": row[0],
            "title": row[1],
            "created_at": row[2].isoformat(),
            "updated_at": row[3].isoformat()
        }

    def find_session_by_id(self, session_id: str, user_id: int) -> dict[str, Any]:
        """查询会话信息"""
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT session_id, title, created_at, updated_at
                    FROM chat_sessions
                    WHERE session_id = %s AND user_id = %s LIMIT 1
                    """,
                    (session_id, user_id)
                )
                row = cur.fetchone()
        return {
            "id": row[0],
            "title": row[1],
            "created_at": row[2].isoformat(),
            "updated_at": row[3].isoformat()
        }

    def find_message_by_id(self, message_id: int):
        """查询消息"""
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM chat_messages
                    WHERE id = %s LIMIT 1
                    """,
                    (message_id,)
                )
                row = cur.fetchone()
        return {
            "id": row[0],
            "session_id": row[1],
            "role": row[2],
            "content": row[3],
            "created_at": row[4].isoformat()
        }

    def find_session_last_message(self, session_id: str):
        """查询消息"""
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, role, content, created_at
                    FROM chat_messages
                    WHERE session_id = %s ORDER BY created_at DESC LIMIT 1
                    """,
                    (session_id,)
                )
                row = cur.fetchone()
        return {
            "id": row[0],
            "session_id": row[1],
            "role": row[2],
            "content": row[3],
            "created_at": row[4].isoformat()
        }


    def delete_session(self, session_id: str) -> None:
        """删除会话及其消息"""
        conn = self.session_store.get_connection()
        try:
            conn.begin()
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_messages WHERE session_id = %s",
                    (session_id,)
                )
            conn.commit()
        except Exception as e:
            raise e
        finally:
            conn.close()

    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """更新会话的metadata"""
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET metadata = %s WHERE session_id = %s",
                    (json.dumps(metadata), session_id)
                )
        logger.debug(f"更新会话metadata: {session_id}")

    def update_session_title(self, session_id: str, title: str) -> bool:
        """更新会话标题，返回是否更新成功"""
        with self.session_store.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET title = %s WHERE session_id = %s",
                    (title, session_id)
                )
                return cur.rowcount > 0

    def get_user_sessions(
            self,
            user_id: int,
            limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        try:
            with self.session_store.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT `session_id`, `user_id`, `title`, `created_at`, `updated_at`
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
                            "title": row[2],
                            "created_at": row[3].isoformat(),
                            "updated_at": row[4].isoformat()
                        })
                    return result_list
        except Exception as e:
            raise e

def create_session_repository(session_store: MySQLSessionStore) -> SessionRepository:
    return SessionRepository(session_store)
