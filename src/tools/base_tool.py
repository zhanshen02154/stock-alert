from dataclasses import dataclass, field
from typing import TypeVar, Any

from pydantic import BaseModel, Field

P = TypeVar("P")
T = TypeVar("T")

@dataclass
class Context:
    session_id: str
    metadata: dict = field(default_factory=dict)

class ToolStatus[Enum]:
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ToolResult(BaseModel):
    """统一返回结构"""
    status: str = Field(description="状态")
    data: Any = Field(description="数据")
    error: str | None = Field(default=None, description="错误信息")

class BaseToolInput(BaseModel):
    """所有工具输入的基类"""
    pass