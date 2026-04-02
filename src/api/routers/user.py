from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from src.api.dependencies import get_user_service
from src.api.schemas import ApiResponse, success, fail
from src.service.user import UserService
from src.utils.jwt import JWTUtil

routers = APIRouter(prefix="/users", tags=["users"])

class LoginRequest(BaseModel):
    """登录请求数据"""
    username: str = Field(description="用户名", min_length=1, max_length=50)
    password: str = Field(description="密码", min_length=1, max_length=100)

class LoginResponse(BaseModel):
    """登录响应数据"""
    access_token: str = Field(description="access_token")
    expires_in: float = Field(description="过期时间(秒)")

@routers.post(path="/login")
async def login(req: LoginRequest, user_service: UserService = Depends(get_user_service)) -> ApiResponse[LoginResponse]:
    """
    用户登录
    :param req: 登录请求数据
    :param user_service: 用户服务层
    :return:
    """
    try:
        token, expires_in = user_service.login(username=req.username, password=req.password)
        # 构建响应
        response_data = LoginResponse(
            access_token=token,
            expires_in=expires_in
        )
        return success(data=response_data)
    except Exception as e:
        return fail(msg=str(e), code=500)

@routers.post(path="/logout")
async def logout(
    authorization: str = Header(..., description="Bearer token"),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[None]:
    """
    用户退出登录
    :param authorization: Bearer token
    :param user_service: 用户服务层
    :return:
    """
    # 提取token
    if not authorization.startswith("Bearer "):
        return fail(msg="无效的Authorization header格式", code=400)
    
    token = authorization.replace("Bearer ", "")
    
    # 验证token并获取用户ID
    user_id = JWTUtil.get_user_id_from_token(token)
    if not user_id:
        return fail(msg="无效的token", code=401)
    
    # 调用服务层退出登录
    success_flag, error_msg = await user_service.logout(user_id=user_id, token=token)
    
    if not success_flag:
        return fail(msg=error_msg, code=500)
    
    return success(data=None)

@routers.get(path="/auth/check")
async def auth_check(
    request: Request,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[None]:
    """
    检查用户登录状态
    :param request: 请求对象
    :param user_service: 用户服务层
    :return:
    """
    # 从中间件获取已验证的user_id
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return fail(msg="未授权", code=401)

    # 检查登录状态
    is_logged_in, error_msg = user_service.check_login_status(user_id)
    if not is_logged_in:
        return fail(msg=error_msg, code=401)

    return success(data=None)