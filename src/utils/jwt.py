import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt


class JWTUtil:
    """JWT工具类"""

    # JWT配置
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS = 7  # token有效期7天

    @classmethod
    def create_access_token(
        cls, user_id: int, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建JWT access token

        Args:
            user_id: 用户ID
            expires_delta: 过期时间增量

        Returns:
            JWT token字符串
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=cls.ACCESS_TOKEN_EXPIRE_DAYS
            )

        payload = {"user_id": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token

    @classmethod
    def verify_token(cls, token: str) -> Optional[dict]:
        """
        验证JWT token

        Args:
            token: JWT token字符串

        Returns:
            解码后的payload，验证失败返回None
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def get_user_id_from_token(cls, token: str) -> Optional[int]:
        """
        从token中获取用户ID

        Args:
            token: JWT token字符串

        Returns:
            用户ID，验证失败返回None
        """
        payload = cls.verify_token(token)
        if payload:
            return payload.get("user_id")
        return None

    @classmethod
    def get_expire_time(cls, token: str) -> Optional[datetime]:
        """
        从token中获取过期时间

        Args:
            token: JWT token字符串

        Returns:
            过期时间，验证失败返回None
        """
        try:
            # 不验证过期时间，只解码
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM],
                options={"verify_exp": False},
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def get_expires_in(cls) -> int:
        """
        获取token过期时间（秒）

        Returns:
            过期时间秒数
        """
        return cls.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
