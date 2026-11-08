from dataclasses import dataclass
from enum import Enum
from typing import Literal, List

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    SUPPLY_CHAIN = "supply_chain"
    INVENTORY = "inventory"


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
        AgentType.SUPPLY_CHAIN,
    ] = Field(description="下一步路由目标")
    next_task: TaskInfo | None = Field(
        description="下一步路由的任务信息（已获得最终答案则为None）", default=None
    )

class KBReferenceItem(BaseModel):
    """
    参考资料来源
    """
    source: str = Field(description="文件名", min_length=1, max_length=60)
    version: str = Field(description="版本", min_length=1, max_length=200)
    context: str = Field(description="上下文（300字内）", min_length=1, max_length=300)

class InventoryResult(BaseModel):
    """
    库存智能助手最终输出结果
    """
    summary: str = Field(description="结论")
    reasoning: str = Field(description="决策理由", min_length=1, max_length=200)
    confidence: float = Field(description="决策置信度", ge=0, le=1)
    references: list[KBReferenceItem] = Field(description="参考的知识库来源（用到知识库时必传）", min_length=0)
    timestamp: int = Field(description="时间戳（单位: s）")

class SessionTitle(BaseModel):
    """
    标题结果
    """
    title: str = Field(description="标题", min_length=1, max_length=50)

@dataclass
class Context:
    user_id: int