from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from src.api.dependencies import get_redis_client_from_app
from src.api.schemas import success, ApiResponse

router = APIRouter(prefix="/check", tags=["health_check"])


@router.get(path="/health")
async def health(redis_client: Redis = Depends(get_redis_client_from_app)) -> ApiResponse[None] | None:
    try:
        resp = await redis_client.ping()
        if resp:
            return success(data=None)
    except BaseException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Redis连接失败: {e}")

@router.get(path="/readiness")
async def readiness(redis_client: Redis = Depends(get_redis_client_from_app)):
    """是否准备好了"""
    try:
        resp = await redis_client.ping()
        if resp:
            return success(data=None)
    except BaseException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Redis连接失败{e}")