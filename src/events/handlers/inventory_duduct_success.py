from typing import Any

from src.events.handlers.base_handler import BaseHandler
from src.events.schemas import OnInventoryDeductSuccess


class InventoryDeductedHandler(BaseHandler):
    """库存扣减事件处理器"""

    @property
    def event_type(self) -> str:
        return "OnInventoryDeductSuccess"

    async def handle(
            self,
            event: OnInventoryDeductSuccess,
            raw_message: dict[str, Any]
    ) -> None:
        pass

    def validate_event(
            self,
            event_data: dict[str, Any]
    ) -> OnInventoryDeductSuccess:
        """验证并解析事件数据"""
        return OnInventoryDeductSuccess(**event_data)