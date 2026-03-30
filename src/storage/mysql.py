import logging
from typing import Dict, Any, Optional

import pymysql
from dbutils.pooled_db import PooledDB

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

    def _get_connection(self):
        """从连接池获取连接"""
        if self.pool is None:
            raise RuntimeError("连接池未初始化，请先调用 initialize()")
        return self.pool.connection()

    def initialize(self) -> None:
        """初始化连接池"""
        if self.pool is not None:
            return

        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=self.config.get("max_connections", 20),
            mincached=self.config.get("min_cached", 2),
            maxcached=self.config.get("max_cached", 5),
            blocking=True,
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 3306),
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
            charset="utf8mb4",
            autocommit=True,
        )
        logger.info("MySQL同步连接池初始化完成")

    def close(self) -> None:
        """关闭连接池"""
        if self.pool:
            try:
                # PooledDB 没有 close 方法，但可以关闭所有缓存的连接
                # 通过关闭连接池中的所有连接来释放资源
                # 注意：PooledDB 本身没有提供 close 方法
                # 连接会在归还时自动管理
                self.pool = None
                logger.info("MySQL连接池已关闭")
            except Exception as e:
                logger.error(f"关闭MySQL连接池失败: {e}", exc_info=True)


def create_mysql_session_store(config: dict[str, Any]) -> MySQLSessionStore:
    return MySQLSessionStore(config=config)
