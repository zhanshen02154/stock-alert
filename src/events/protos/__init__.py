"""Protobuf 消息模块"""
from .base_event_pb2 import BaseEvent
from .product_event_pb2 import OnInventoryDeductSuccess, SkuInfo

# 事件类型到 protobuf 消息类的映射
EVENT_TYPE_TO_PROTOBUF = {
    "OnInventoryDeductSuccess": OnInventoryDeductSuccess,
}

__all__ = [
    'BaseEvent',
    'OnInventoryDeductSuccess',
    'SkuInfo',
    'EVENT_TYPE_TO_PROTOBUF',
]
