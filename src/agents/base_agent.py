from abc import ABC
from typing import Optional, Dict, Any

class BaseAgent(ABC):
    def __init__(self, agent_name: str, llm_config: Optional[Dict] = None):
        self.agent_name = agent_name