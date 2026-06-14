from dataclasses import dataclass
from typing import Literal, List

from pydantic import BaseModel, Field


class AgentType:
    SUPERVISOR = "supervisor"
    KNOWLEDGES = "knowledges"
    SUPPLY_CHAIN = "supply_chain"


class TaskStatus:
    """
    任务状态
    """

    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskInfo(BaseModel):
    """
    当前任务信息
    """

    id: str = Field(description="任务ID（通过UUID）生成")
    description: str = Field(description="任务详情")
    target: str = Field(description="任务目标")
    agent_type: Literal[
        "FINISH",
        AgentType.KNOWLEDGES,
        AgentType.SUPPLY_CHAIN,
    ] = Field(description="助手标识")
    timeliness: bool = Field(
        description="时效性要求（true=是，false=否）", default=True
    )
    parameters: dict = Field(description="槽位(如sku_code)")


class TaskResult(BaseModel):
    """
    任务执行结果
    """

    id: str = Field(description="任务ID")
    result: str = Field(description="结果")
    agent_type: Literal[
        AgentType.KNOWLEDGES,
        AgentType.SUPPLY_CHAIN,
    ] = Field(description="助手标识")
    confidence: float = Field(description="回答置信度，0到1之间")
    status: Literal[TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED] = (
        Field(
            description="状态: completed=执行成功 failed=执行失败 blocked=执行异常"
        )
    )
    needs: List[str] = Field(default=[], description="缺少的数据")
    timestamp: int = Field(description="时间戳（单位秒,UTC+8）")


class Router(BaseModel):
    """
    Supervisor路由，决定下一个Worker
    """

    reasoning: str = Field(description="决策原因")
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
