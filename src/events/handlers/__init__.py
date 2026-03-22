"""Handlers 模块 - 自动注册所有事件处理器"""

from .base_handler import BaseHandler
from .handler_registry import registry, register_handler
from .inventory_duduct_success import InventoryDeductedHandler

# 注册所有处理器
registry.register(InventoryDeductedHandler())

__all__ = [
    "BaseHandler",
    "registry",
    "register_handler",
    "InventoryDeductedHandler",
]