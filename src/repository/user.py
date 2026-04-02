from typing import Optional, Dict, Any
from datetime import datetime

from src.storage import MySQLSessionStore


class UserRepository:
    """用户仓库 - 同步实现"""
    def __init__(self, session_store: MySQLSessionStore):
        self.session_store = session_store
    
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名查询用户
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典，不存在返回None
        """
        conn = self.session_store.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id, username, password, last_login_time, is_login, created_at, updated_at FROM users WHERE username = %s LIMIT 1"
                cursor.execute(sql, (username,))
                result = cursor.fetchone()
                if result:
                    return {
                        "id": result[0],
                        "username": result[1],
                        "password": result[2],
                        "last_login_time": result[3],
                        "is_login": result[4],
                        "created_at": result[5],
                        "updated_at": result[6]
                    }
                return None
        finally:
            conn.close()
    
    def update_last_login_time(self, user_id: int, login_time: datetime) -> bool:
        """
        更新用户最后登录时间并标记为已登录
        
        Args:
            user_id: 用户ID
            login_time: 登录时间
            
        Returns:
            更新成功返回True，否则返回False
        """
        conn = self.session_store.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE users SET last_login_time = %s, is_login = 2, updated_at = %s WHERE id = %s"
                cursor.execute(sql, (login_time, login_time, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except BaseException as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID查询用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，不存在返回None
        """
        conn = self.session_store.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id, username, is_login FROM users WHERE id = %s LIMIT 1"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        "id": result[0],
                        "username": result[1],
                        "is_login": result[2]
                    }
                return None
        finally:
            conn.close()

    def update_logout_status(self, user_id: int) -> bool:
        """
        更新用户退出登录状态

        Args:
            user_id: 用户ID

        Returns:
            更新成功返回True，否则返回False
        """
        conn = self.session_store.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE users SET is_login = 1, updated_at = %s WHERE id = %s"
                cursor.execute(sql, (datetime.now(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except BaseException as e:
            conn.rollback()
            raise e
        finally:
            conn.close()