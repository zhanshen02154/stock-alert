from typing import List

from langchain_core.messages import AnyMessage
from langgraph.graph import MessagesState

from src.core.schemas import TaskInfo


class TaskStatus:
    """
    任务状态
    """

    PENDING = "pending"  # 待执行
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class AgentState(MessagesState):
    """
    Agent全局状态
    """

    next: str  # 决定下一步的操作
    summarized_messages: List[AnyMessage]  # 总结的消息
    task: TaskInfo  # 任务信息
