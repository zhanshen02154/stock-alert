from typing import TypeVar, Generic

from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(description="状态码", default=0)
    msg: str  = Field(description="状态信息", default="success")
    data: T | None = Field(description="数据", default=None)

class ChatRequest(BaseModel):
    """聊天请求数据"""
    content: str = Field(description="消息内容")
    chat_id: str = Field(description="会话ID")


class ChatResponse(BaseModel):
    """聊天响应数据"""
    message_id: int = Field(description="消息ID")
    content: str = Field(description="消息内容")


class SessionUpdateRequest(BaseModel):
    """会话更新请求数据"""
    chat_id: str = Field(description="会话ID")
    chat_name: str = Field(description="会话标题")

class ChatAiRequest(BaseModel):
    """聊天AI请求数据"""
    chat_id: str = Field(description="会话ID")


class MessagesRequest(BaseModel):
    """消息请求数据"""
    chat_id: str = Field(description="会话ID", max_length=100)


def success(data: T) -> ApiResponse[T]:
    """返回成功数据"""
    data = ApiResponse[T](data=data, msg="success", code=0)
    return data


def fail(msg: str, code: int = 9999) -> ApiResponse:
    """返回失败数据"""
    return ApiResponse(data=None, msg=msg, code=code)