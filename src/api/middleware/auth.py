import json
import logging
from fastapi import status
from starlette.types import ASGIApp, Receive, Scope, Send
from src.storage import RedisClient
from src.utils.jwt import JWTUtil

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Token验证中间件 - ASGI App方式"""

    # 排除不需要验证的路由
    EXCLUDED_PATHS = {
        "/api/v1/users/login",
        "/api/v1/check/health",
        "/api/v1/check/readiness",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    # 需要从URL参数获取token的路由
    TOKEN_FROM_QUERY_PATHS = {
        '/api/v1/chats/ai-response'  # SSE接口，token通过querystring传递
    }

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI App 入口"""
        # 只处理 HTTP 请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 获取请求路径
        path = scope.get("path", "")
        logger.info(f"path: {path}")

        # 检查是否在排除列表中
        if path in self.EXCLUDED_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            await self.app(scope, receive, send)
            return

        token = None
        
        # 检查是否需要从URL参数获取token
        if path in self.TOKEN_FROM_QUERY_PATHS:
            # 从URL查询参数获取token
            query_string = scope.get("query_string", b"").decode("utf-8")
            if query_string:
                params = dict(param.split("=") for param in query_string.split("&"))
                token = params.get("token", "")
        
        # 如果没有从URL参数获取到token，尝试从headers获取
        if not token:
            # 从 headers 获取 Authorization
            headers = dict(scope.get("headers", []))
            authorization = headers.get(b"authorization", b"").decode("utf-8")

            if not authorization:
                # 对于需要token的接口，如果没有token，继续执行（允许无状态访问）
                if path in self.TOKEN_FROM_QUERY_PATHS:
                    # 设置默认 user_id 为 0
                    if "state" not in scope:
                        scope["state"] = {}
                    scope["state"]["user_id"] = 0
                    await self.app(scope, receive, send)
                    return
                await self._send_unauthorized(send, "缺少Authorization header")
                return

            # 验证 Bearer 格式
            if not authorization.startswith("Bearer "):
                await self._send_unauthorized(send, "无效的Authorization header格式")
                return

            # 提取 token
            token = authorization.replace("Bearer ", "")

        # 从 token 中获取 user_id
        user_id = JWTUtil.get_user_id_from_token(token)
        if not user_id:
            await self._send_unauthorized(send, "无效的token")
            return

        # 从 app.state 获取 redis_client
        app_state = scope.get("app")
        if app_state and hasattr(app_state, "state"):
            redis_client: RedisClient = getattr(app_state.state, "redis_client", None)
        else:
            redis_client = None

        if not redis_client:
            logger.error("无法获取 Redis 客户端")
            await self._send_unauthorized(send, "认证服务异常")
            return

        # 检查 token 是否在黑名单中
        blacklist_key = f"token_blacklist:{user_id}"
        try:
            blacklisted_token = await redis_client.aget(blacklist_key)
            if blacklisted_token and blacklisted_token == token:
                await self._send_unauthorized(send, "token已失效")
                return
        except Exception as e:
            logger.error(f"检查token黑名单失败: {e}")
            await self._send_unauthorized(send, "认证服务异常")
            return

        # 将 user_id 存储到 scope["state"] 中，供后续使用
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["user_id"] = user_id

        # 调用下一个 ASGI App
        await self.app(scope, receive, send)

    async def _send_unauthorized(self, send: Send, message: str) -> None:
        """发送 401 响应"""
        response_body = json.dumps({
            "code": status.HTTP_401_UNAUTHORIZED,
            "msg": message,
            "data": None
        }).encode("utf-8")

        await send({
            "type": "http.response.start",
            "status": status.HTTP_401_UNAUTHORIZED,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(response_body)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": response_body,
        })