import logging
from typing import Dict, Any, Optional

import pymysql
from dbutils.pooled_db import PooledDB, PooledSharedDBConnection, PooledDedicatedDBConnection

from config.settings import get_storage_config
from src.storage import SessionStore

logger = logging.getLogger(__name__)


class MySQLSessionStore(SessionStore):
    """MySQL会话存储实现 - 同步连接池"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化MySQL连接池配置

        Args:
            config: MySQL配置，包含 host, port, user, password, database
        """
        self.config = config
        self.pool: Optional[PooledDB] = None
        self.__initialize()

    def get_connection(self) -> PooledSharedDBConnection | PooledDedicatedDBConnection:
        """从连接池获取连接"""
        if self.pool is None:
            self.__initialize()
        return self.pool.connection()

    def __initialize(self) -> None:
        """初始化连接池"""
        if self.pool is not None:
            return
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=self.config.get("max_connections", 30),
            mincached=self.config.get("min_cached", 5),
            maxcached=self.config.get("max_cached", 20),
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 3306),
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
            charset="utf8mb4",
            autocommit=False,
            ping=1
        )
        logger.info("MySQL同步连接池初始化完成")

    def close(self) -> None:
        """关闭连接池"""
        if self.pool:
            try:
                self.pool.close()
                logger.info("MySQL连接池已关闭")
            except Exception as e:
                logger.error(f"关闭MySQL连接池失败: {e}", exc_info=True)

def create_mysql_session_store() -> MySQLSessionStore:
    conf = get_storage_config("mysql")
    return MySQLSessionStore(config=conf)
