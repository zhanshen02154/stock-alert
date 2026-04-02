import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status
from src.storage import RedisClient
from src.utils.jwt import JWTUtil

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Token验证中间件"""

    # 排除不需要验证的路由
    EXCLUDED_PATHS = {
        "/api/v1/users/login",
        "/api/v1/check/health",
        "/api/v1/check/readiness",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """中间件调度方法"""
        # 获取请求路径
        path = request.url.path

        # 检查是否在排除列表中
        if path in self.EXCLUDED_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        # 从Header获取Authorization
        authorization = request.headers.get("Authorization")
        if not authorization:
            return self._unauthorized_response("缺少Authorization header")

        # 验证Bearer格式
        if not authorization.startswith("Bearer "):
            return self._unauthorized_response("无效的Authorization header格式")

        # 提取token
        token = authorization.replace("Bearer ", "")

        # 从token中获取user_id
        user_id = JWTUtil.get_user_id_from_token(token)
        if not user_id:
            return self._unauthorized_response("无效的token")

        # 从app.state获取redis_client
        redis_client: RedisClient = request.app.state.redis_client

        # 检查token是否在黑名单中
        blacklist_key = f"token_blacklist:{user_id}"
        try:
            blacklisted_token = await redis_client.aget(blacklist_key)
            if blacklisted_token and blacklisted_token == token:
                return self._unauthorized_response("token已失效")
        except Exception as e:
            logger.error(f"检查token黑名单失败: {e}")
            return self._unauthorized_response("认证服务异常")

        # 将user_id存储到request.state中，供后续使用
        request.state.user_id = user_id

        return await call_next(request)

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """返回401响应"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "code": status.HTTP_401_UNAUTHORIZED,
                "msg": message,
                "data": None
            }
        )
