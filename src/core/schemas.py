from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class AgentType:
    SUPERVISOR = "supervisor"
    KNOWLEDGES = "knowledges"
    SUPPLY_CHAIN = "supply_chain"


class TaskInfo(BaseModel):
    """
    当前任务信息
    """

    id: str = Field(description="任务ID（通过UUID）生成")
    description: str = Field(description="任务详情")
    target: str = Field(description="任务目标")
    parameters: dict[str, str] = Field(description="槽位（如商品SKU为sku_code）")
    timeliness: bool = Field(
        description="时效性要求（true=是，false=否）", default=True
    )


class Router(BaseModel):
    """
    Supervisor路由，决定下一个Worker
    """

    reasoning: str = Field(
        description="逐步分析：1)用户意图包含哪些子任务 2)哪些已完成 3)哪些未完成需要派发"
    )
    confidence: float = Field(description="对路由决策的置信度，0到1之间")
    next: Literal[
        "FINISH",
        AgentType.KNOWLEDGES,
        AgentType.SUPPLY_CHAIN,
    ] = Field(description="下一步路由目标")

    next_task: TaskInfo | None = Field(
        description="下一步路由的任务信息（已获得最终答案则为None）", default=None
    )


@dataclass
class Context:
    user_id: int
