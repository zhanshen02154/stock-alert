import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from redis.asyncio import Redis
from src.repository.user import UserRepository
from src.utils.jwt import JWTUtil
from src.utils.password import PasswordUtil


class UserService:
    """用户服务层"""
    def __init__(self, user_repo: UserRepository, redis_client: Redis):
        self.user_repo = user_repo
        self.redis_client = redis_client
    
    def login(self, username: str, password: str) -> Tuple[Optional[str], Optional[float]]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (token, error_message) - 登录成功返回token，失败返回错误信息
        """
        # 查询用户
        try:
            user = self.user_repo.find_by_username(username)
            if not user:
                raise Exception("用户名或密码错误")

            if user["is_login"] == 2:
                raise Exception("用户已登录")

            # 验证密码
            if not PasswordUtil.verify_password(password, user["password"]):
                raise Exception("用户名或密码错误")

            # 生成JWT token
            token = JWTUtil.create_access_token(user_id=user["id"])

            # 更新最后登录时间
            latest_time = datetime.now(timezone.utc)
            self.user_repo.update_last_login_time(
                user_id=user["id"],
                login_time=latest_time
            )
            expire = latest_time + timedelta(seconds=JWTUtil.get_expires_in())

            return token, expire.timestamp()
        except Exception as e:
            raise e
    
    def get_token_expires_in(self) -> int:
        """
        获取token过期时间（秒）
        
        Returns:
            过期时间秒数
        """
        return JWTUtil.get_expires_in()
    
    async def logout(self, user_id: int, token: str) -> Tuple[bool, Optional[str]]:
        """
        用户退出登录

        Args:
            user_id: 用户ID
            token: JWT token

        Returns:
            (success, error_message) - 退出成功返回True，失败返回错误信息
        """
        try:
            # 获取token过期时间
            expire_time = JWTUtil.get_expire_time(token)
            latest_time = datetime.now(timezone.utc)

            # 如果token还未过期，将其加入黑名单
            if expire_time and expire_time > latest_time:
                # 计算过期时间差（秒）
                time_diff = (expire_time - latest_time).total_seconds()

                # 加上3到5分钟的随机值
                random_minutes = random.randint(3, 5) * 60
                cache_ttl = int(time_diff + random_minutes)

                # 将token加入黑名单
                blacklist_key = f"token_blacklist:{user_id}"
                await self.redis_client.setex(
                    blacklist_key,
                    cache_ttl,
                    token
                )

            # 更新用户登录状态为未登录
            self.user_repo.update_logout_status(user_id)

            return True, None
        except Exception as e:
            return False, f"退出登录失败: {str(e)}"

    def check_login_status(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        检查用户登录状态

        Args:
            user_id: 用户ID

        Returns:
            (is_logged_in, error_message) - 已登录返回True，未登录返回False及错误信息
        """
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False, "用户不存在"
        if user["is_login"] == 1:
            return False, "用户未登录"
        return True, None