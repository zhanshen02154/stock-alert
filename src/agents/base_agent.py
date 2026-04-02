from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from langchain_core.tools import BaseTool


class BaseAgent(ABC):
    """Agent基类"""

    tools: List[BaseTool] = []

    def __init__(self, agent_name: str, llm_config: Optional[Dict] = None):
        self.agent_name = agent_name

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    def healthz(self) -> bool:
        pass
