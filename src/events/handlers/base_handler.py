from abc import ABC, abstractmethod
from typing import Any, Dict

from src.events.schemas import BaseEvent

class BaseHandler(ABC):
    """事件处理基类"""

    @property
    @abstractmethod
    def event_type(self) -> str:
        pass

    @abstractmethod
    async def handle(self, event: BaseEvent, raw_message: Dict[str, Any]):
        pass

    # 验证事件
    def validate(self, event_data: Dict[str, Any]) -> BaseEvent:
        pass
