from typing import Any, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.params import Query
from src.api.dependencies import get_session_service
from src.api.schemas import ApiResponse, fail, success, MessagesRequest
from src.service.session import SessionService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get(path="/all")
async def get_all_sessions(req: Request, session_service: SessionService = Depends(get_session_service)) -> ApiResponse[list[dict[str, Any]]]:
    """获取所有会话列表"""
    try:
        user_id: int = req.state.user_id
        if user_id == 0:
            return fail(msg="未登录", code=401)
        sessions = session_service.get_user_sessions(user_id=user_id)
        return success(data=sessions)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/messages")
async def get_session_messages(req: Annotated[MessagesRequest, Query()], session_service: SessionService = Depends(get_session_service)) -> ApiResponse[list[dict[str, Any]]]:
    try:
        print(req.chat_id)
        messages = session_service.get_session_history(req.chat_id)
        return success(data=messages)
    except Exception as e:
        raise e


@router.delete("/{chat_id}")
async def remove_session(chat_id: str, session_service: SessionService = Depends(get_session_service)) -> ApiResponse[None]:
    try:
        await session_service.delete_session(chat_id)
        return success(data=None)
    except Exception as e:
        raise e


@router.post("/new")
async def create_session(req: Request, session_service: SessionService = Depends(get_session_service)) -> ApiResponse[dict[str, Any]]:
    """创建新会话"""
    try:
        user_id: int = req.state.user_id
        if user_id == 0:
            return fail(msg="未登录", code=401)
        
        import uuid
        session_id = str(uuid.uuid4())
        session_info = session_service.create_session(
            session_id=session_id,
            user_id=str(user_id),
            title="新对话"
        )
        return success(data=session_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))