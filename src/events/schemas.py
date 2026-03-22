"""事件数据模型"""
from datetime import datetime
from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件类型枚举"""
    INVENTORY_DEDUCT_SUCCESS = "OnInventoryDeductSuccess"  # 库存扣减成功


class BaseEvent(BaseModel):
    """事件基类"""
    event_id: str = Field(..., description="事件唯一ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间戳")
    source: str = Field(default="unknown", description="事件来源服务")
    schema_version: str = Field(default="1.0", description="事件版本")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SkuInfo(BaseModel):
    """SKU 信息"""
    id: int = Field(..., alias="Id", description="SKU ID")
    quantity: int = Field(..., alias="Quantity", description="扣减数量")
    stock: int = Field(..., alias="Stock", description="剩余库存")
    threshold: int = Field(..., alias="Threshold", description="阈值")
    
    class Config:
        populate_by_name = True  # 允许通过字段名或别名赋值
        json_schema_extra = {
            "example": {
                "Id": 1001,
                "Quantity": 10,
                "Stock": 90,
                "Threshold": 80
            }
        }


class OnInventoryDeductSuccess(BaseEvent):
    """库存扣减成功事件
    
    对应 protobuf 定义：
    message OnInventoryDeductSuccess {
        int64 OrderId = 1;
        repeated SkuInfo Sku = 2;
    }
    """
    event_type: str = EventType.INVENTORY_DEDUCT_SUCCESS.value
    order_id: int = Field(..., alias="OrderId", description="订单ID")
    sku_list: list[SkuInfo] = Field(
        default_factory=list, 
        alias="Sku", 
        description="SKU 列表"
    )
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "event_id": "evt_123456",
                "event_type": "OnInventoryDeductSuccess",
                "OrderId": 12345,
                "Sku": [
                    {
                        "Id": 1001,
                        "Quantity": 10,
                        "Stock": 90,
                        "Threshold": 80
                    },
                    {
                        "Id": 1002,
                        "Quantity": 5,
                        "Stock": 50,
                        "Threshold": 80
                    }
                ],
                "source": "product-service",
                "schema_version": "1.0.0"
            }
        }


# 事件类型到模型的映射
EVENT_TYPE_TO_MODEL: Dict[str, type] = {
    EventType.INVENTORY_DEDUCT_SUCCESS.value: OnInventoryDeductSuccess,
}
