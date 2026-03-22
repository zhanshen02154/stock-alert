"""
会话存储模块 - MySQL实现
"""
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiomysql

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """会话存储抽象基类"""

    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """保存消息，返回消息ID"""
        pass

    @abstractmethod
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        pass

    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建新会话"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass


class MySQLSessionStore(SessionStore):
    """MySQL会话存储实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化MySQL连接池
        
        Args:
            config: MySQL配置，包含 host, port, user, password, database
        """
        self.config = config
        self.pool: Optional[aiomysql.Pool] = None
        self._create_tables_sql = """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(64),
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS chat_messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            role ENUM('user', 'assistant', 'system') NOT NULL,
            content TEXT NOT NULL,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_id (session_id),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

    async def initialize(self) -> None:
        """初始化连接池和表结构"""
        self.pool = await aiomysql.create_pool(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 3306),
            user=self.config["user"],
            password=self.config["password"],
            db=self.config["database"],
            charset="utf8mb4",
            autocommit=True,
            minsize=1,
            maxsize=10
        )
        
        # 创建表结构
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(self._create_tables_sql)
        
        logger.info("MySQL会话存储初始化完成")

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建新会话"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, metadata)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, user_id, json.dumps(metadata or {}))
                )
        logger.debug(f"创建会话: {session_id}")

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """保存消息"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, metadata)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, role, content, json.dumps(metadata or {}))
                )
                message_id = cur.lastrowid
                
                # 更新会话时间
                await cur.execute(
                    "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (session_id,)
                )
        
        logger.debug(f"保存消息: session={session_id}, role={role}")
        return message_id

    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
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
                
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                
                return [
                    {
                        "id": row["id"],
                        "role": row["role"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"].isoformat()
                    }
                    for row in rows
                ]

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT session_id, user_id, metadata, created_at, updated_at
                    FROM chat_sessions
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                rows = await cur.fetchall()
                
                return [
                    {
                        "session_id": row["session_id"],
                        "user_id": row["user_id"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat()
                    }
                    for row in rows
                ]

    async def delete_session(self, session_id: str) -> None:
        """删除会话及其消息"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM chat_sessions WHERE session_id = %s",
                    (session_id,)
                )
        logger.info(f"删除会话: {session_id}")

    async def close(self) -> None:
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL连接池已关闭")
