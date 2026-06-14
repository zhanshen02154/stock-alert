import operator
from typing import Annotated, List

from langgraph.graph import MessagesState

from src.core.schemas import TaskInfo, TaskResult


class AgentState(MessagesState):
    """
    Agent全局状态
    """

    next: str  # 决定下一步的操作

    task: TaskInfo | None  # 确定任务

    completed_task: Annotated[List[TaskInfo], operator.add]  # 已完成的任务

    user_input: str  # 用户输入

    finished_tasks: Annotated[List[TaskResult], operator.add]  # 存储已完成的任务的结果
