import logging
from typing import Dict, Any, List

import pymysql
from dbutils.pooled_db import (
    PooledDB,
)

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
        self._pools: Dict[str, PooledDB] = {}
        self.__initialize()

    def get_connection(self, connection: str = "default"):
        """从连接池获取连接"""
        if connection in self._pools:
            return self._pools[connection].connection()
        return None

    def __initialize(self) -> None:
        """初始化连接池"""
        for key, value in self.config.items():
            self._pools[key] = PooledDB(
                creator=pymysql,
                maxconnections=value.get("max_connections", 30),
                mincached=value.get("min_cached", 5),
                maxcached=value.get("max_cached", 20),
                host=value.get("host", "localhost"),
                port=value.get("port", 3306),
                user=value.get("user", "local"),
                password=value.get("password", ""),
                database=value.get("database"),
                charset="utf8mb4",
                autocommit=True,
                ping=1,
            )
        logger.info("MySQL同步连接池初始化完成")

    def query(
        self, sql: str, params: tuple | None = None, connection: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        执行SELECT或SHOW查询语句，支持参数绑定

        Args:
            sql: SQL查询语句，只允许SELECT和SHOW语句
            params: SQL参数绑定，元组形式，用于防止SQL注入
            connection: 连接池名称，默认为"default"

        Returns:
            List[Dict[str, Any]]: 查询结果列表，每行为一个字典

        Raises:
            ValueError: 如果SQL语句不是SELECT或SHOW语句
            Exception: 数据库执行错误
        """
        sql_upper = sql.strip().upper()
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW")):
            raise ValueError("只允许执行SELECT和SHOW语句")

        pool = self.get_connection(connection)
        if not pool:
            raise ValueError(f"连接池 {connection} 不存在")

        conn = None
        cursor = None
        try:
            with self.get_connection(connection) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or ())
                    results = cursor.fetchall()
                    return results
        except Exception as e:
            logger.error(f"MySQL查询执行失败: {e}", exc_info=True)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute(
        self, sql: str, params: tuple | None = None, connection: str = "default"
    ) -> int:
        """
        执行INSERT/UPDATE/DELETE语句，支持参数绑定

        Args:
            sql: SQL语句，支持INSERT、UPDATE、DELETE等写操作
            params: SQL参数绑定，元组形式，用于防止SQL注入
            connection: 连接池名称，默认为"default"

        Returns:
            int: 影响的行数

        Raises:
            ValueError: 如果SQL语句是SELECT或SHOW语句（应该使用query方法）
            Exception: 数据库执行错误
        """
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW"):
            raise ValueError("SELECT和SHOW语句请使用query方法")

        conn = None
        cursor = None
        try:
            conn = self.get_connection(connection)
            if not conn:
                raise ValueError(f"连接池 {connection} 不存在")
            
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, params or ())
                conn.commit()
                return affected_rows
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"MySQL执行失败: {e}", exc_info=True)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def close(self) -> None:
        """关闭连接池"""
        if self._pools:
            try:
                for key, value in self._pools.items():
                    value.close()
                logger.info("MySQL连接池已关闭")
            except Exception as e:
                logger.error(f"关闭MySQL连接池失败: {e}", exc_info=True)


# 全局MySQL会话存储实例
_mysql_session_store: MySQLSessionStore | None = None


def create_mysql_session_store() -> MySQLSessionStore:
    """创建MySQL会话存储实例"""
    conf = get_storage_config("mysql")
    return MySQLSessionStore(config=conf)


def get_mysql_session_store() -> MySQLSessionStore:
    """获取全局MySQL会话存储实例"""
    global _mysql_session_store
    if _mysql_session_store is None:
        _mysql_session_store = create_mysql_session_store()
    return _mysql_session_store


def init_mysql_session_store() -> None:
    """初始化全局MySQL会话存储实例"""
    global _mysql_session_store
    if _mysql_session_store is None:
        _mysql_session_store = create_mysql_session_store()
        logger.info("全局MySQL会话存储实例已初始化")


def close_mysql_session_store() -> None:
    """关闭全局MySQL会话存储实例"""
    global _mysql_session_store
    if _mysql_session_store is not None:
        _mysql_session_store.close()
        _mysql_session_store = None
        logger.info("全局MySQL会话存储实例已关闭")
