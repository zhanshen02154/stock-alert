import dataclasses
import json
from typing import Any, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.params import Query
from fastapi.sse import ServerSentEvent, EventSourceResponse
from src.api.dependencies import get_session_service, get_chat_service
from src.api.schemas import ApiResponse, fail, success, MessagesRequest, ChatRequest, ChatResponse, \
    SessionUpdateRequest, ChatAiRequest
from src.service.chat import ChatService
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

@router.post("/messages/add")
async def add_message(req: Request, params: Annotated[ChatRequest, Form()], chat_svc: ChatService = Depends(get_chat_service)):
    try:
        user_id: int = req.state.user_id
        message_id = chat_svc.add_message(message=params.content, session_id=params.chat_id, user_id=user_id)
        return success(data=ChatResponse(message_id=message_id, content=params.content))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/update")
async def update(req: Request, params: SessionUpdateRequest, session_service: SessionService = Depends(get_session_service)):
    try:
        user_id: int = req.state.user_id
        session_service.update(session_id=params.chat_id, title=params.chat_name, user_id=user_id)
        return success(data={"chat_id": params.chat_id, "chat_name": params.chat_name})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/ai-response")
async def get_ai_response(req: Annotated[ChatAiRequest, Query()], chat_svc: ChatService = Depends(get_chat_service)):
    """获取AI流式响应"""

    async def event_generator():
        try:
            async for message in chat_svc.chat_astream(session_id=req.chat_id):
                sse_event = ServerSentEvent(data=json.dumps(dataclasses.asdict(message)), event=message.type, retry=5000)
                yield f"data: {sse_event.data}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return EventSourceResponse(event_generator(), media_type="text/event-stream", headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'X-Accel-Buffering': 'no'
    })
