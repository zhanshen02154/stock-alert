from typing import Literal

from pydantic import BaseModel

from src.core.agent_state import AgentType


class Router(BaseModel):
    """
    Supervisor路由，决定下一个Worker
    """

    next: Literal[AgentType.DATA_QUERY, "FINISH"]
