from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class AgentType:
    SUPERVISOR = "supervisor"
    DATA_QUERY = "data_query"
    KNOWLEDGE_SEARCH = "knowledge_search"
    UNKNOWN = "unknown"
    INVENTORY_OPERATOR = "inventory_operator"
    SUPPLIER = "supplier"


class TaskInfo(BaseModel):
    description: str = Field(description="任务详情")
    background: str = Field(description="任务背景")
    target: str = Field(description="任务目标")
    timeliness: bool = Field(
        description="时效性要求（true=是，false=否）", default=True
    )


class Router(BaseModel):
    """
    Supervisor路由，决定下一个Worker
    """

    next: Literal[
        AgentType.DATA_QUERY,
        "FINISH",
        AgentType.SUPERVISOR,
        AgentType.KNOWLEDGE_SEARCH,
        AgentType.INVENTORY_OPERATOR,
        AgentType.SUPPLIER,
    ]

    task: TaskInfo = Field(description="下一个任务的信息", default=None)


@dataclass
class Context:
    user_id: int
