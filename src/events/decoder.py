"""事件解码器 - 处理 Protobuf 消息的解码和转换"""
import base64
import logging
from typing import Any
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError

from .protos import BaseEvent, EVENT_TYPE_TO_PROTOBUF
from .schemas import (
    EVENT_TYPE_TO_MODEL, 
    BaseEvent as PydanticBaseEvent
)


logger = logging.getLogger(__name__)


class EventDecoder:
    """事件解码器
    
    负责将 Kafka 消息解码为 Pydantic 事件对象
    支持的格式：
    - Header: 消息头，包含 Event-Id, Timestamp, Event-Type
    - Body: Base64 编码的 BaseEvent protobuf 消息
    - Payload: 具体事件内容的 protobuf 字节
    """
    
    @staticmethod
    def decode_kafka_message(
        message_value: bytes,
        encoding: str = "protobuf"
    ) -> tuple[dict[str, Any], PydanticBaseEvent]:
        """
        解码 Kafka 消息
        
        Args:
            message_value: Kafka 消息的 value 字节
            encoding: 编码格式，支持 "protobuf" 或 "json"
            
        Returns:
            (header, event) 元组，event 是 Pydantic 事件对象
            
        Raises:
            ValueError: 消息格式错误
        """
        import json
        
        # 解析 JSON 外层结构
        try:
            message_dict = json.loads(message_value.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"消息 JSON 解析失败: {e}")
        
        # 提取 Header 和 Body
        header = message_dict.get('Header', {})
        body = message_dict.get('Body', '')
        
        if not header:
            raise ValueError("消息缺少 Header 字段")
        
        if not body:
            raise ValueError("消息缺少 Body 字段")
        
        # 根据 encoding 解码 Body
        if encoding == "protobuf":
            event = EventDecoder.decode_protobuf_body(body, header)
        else:
            # 其他编码格式（如纯 JSON）
            body_dict = json.loads(body) if isinstance(body, str) else body
            event_type = header.get('Event-Type')
            event = EventDecoder.to_pydantic_event(event_type, body_dict)
        
        return header, event
    
    @staticmethod
    def decode_protobuf_body(
        body_base64: str,
        header: dict[str, Any]
    ) -> PydanticBaseEvent:
        """
        解码 Protobuf Body
        
        Args:
            body_base64: Base64 编码的 BaseEvent protobuf 消息
            header: 消息头
            
        Returns:
            Pydantic 事件对象
        """
        # Base64 解码
        try:
            body_bytes = base64.b64decode(body_base64)
        except Exception as e:
            raise ValueError(f"Base64 解码失败: {e}")
        
        # 反序列化 BaseEvent
        try:
            base_event = BaseEvent()
            base_event.ParseFromString(body_bytes)
        except DecodeError as e:
            raise ValueError(f"BaseEvent Protobuf 反序列化失败: {e}")
        
        # 从 BaseEvent 提取信息
        event_type = header.get('Event-Type', '')
        timestamp = base_event.timestamp
        payload_bytes = base_event.payload
        
        # 从 header 提取 event_id
        event_id = header.get('Event_id', header.get('Event_id', ''))
        
        # 反序列化 payload 为具体事件
        event_data = EventDecoder.decode_payload(
            event_type,
            payload_bytes,
            header
        )
        
        # 添加元数据
        event_data['event_id'] = event_id
        event_data['event_type'] = event_type
        event_data['timestamp'] = timestamp
        event_data['micro-topic'] = header.get("Micro-Topic", "")
        event_data['pkey'] = header.get("Pkey", "")
        event_data['schema_version'] = header.get("Schema_version", "")
        event_data['trace_id'] = header.get("Trace_id", "")
        event_data['source'] = header.get("Source", "")
        event_data['traceparent'] = header.get("Traceparent", "")

        # 转换为 Pydantic 模型
        return EventDecoder.to_pydantic_event(event_type, event_data)
    
    @staticmethod
    def decode_payload(
        event_type: str,
        payload_bytes: bytes,
        header: dict[str, Any]
    ) -> dict[str, Any]:
        """
        解码 Payload 为具体事件
        
        Args:
            event_type: 事件类型
            payload_bytes: Payload 字节
            header: 消息头
            
        Returns:
            事件数据字典
        """
        # 获取对应的 protobuf 消息类
        protobuf_class = EVENT_TYPE_TO_PROTOBUF.get(event_type)
        
        if not protobuf_class:
            logger.warning(
                "未找到事件类型 '%s' 的 Protobuf 定义，"
                "返回空 payload",
                event_type
            )
            return {}
        
        # 反序列化 payload
        try:
            protobuf_message = protobuf_class()
            protobuf_message.ParseFromString(payload_bytes)
        except DecodeError as e:
            raise ValueError(
                f"事件类型 '{event_type}' 的 Payload 反序列化失败: {e}"
            )
        
        # 转换为字典（保留原始字段名）
        event_dict = MessageToDict(
            protobuf_message,
            preserving_proto_field_name=True,  # 保留原始字段名
            use_integers_for_enums=True
        )
        
        return event_dict
    
    @staticmethod
    def to_pydantic_event(
        event_type: str,
        event_data: dict[str, Any]
    ) -> PydanticBaseEvent:
        """
        将事件数据转换为 Pydantic 模型
        
        Args:
            event_type: 事件类型
            event_data: 事件数据字典
            
        Returns:
            Pydantic 事件对象
        """
        event_model = EVENT_TYPE_TO_MODEL.get(event_type)
        
        if not event_model:
            logger.warning(
                "未找到事件类型 '%s' 的 Pydantic 模型，"
                "使用 BaseEvent",
                event_type
            )
            event_model = PydanticBaseEvent
        
        return event_model(**event_data)


# 便捷函数
def decode_message(
    message_value: bytes,
    encoding: str = "protobuf"
) -> tuple[dict[str, Any], PydanticBaseEvent]:
    """
    解码 Kafka 消息为 Pydantic 事件对象
    
    Args:
        message_value: Kafka 消息 value
        encoding: 编码格式
        
    Returns:
        (header, event) 元组
    """
    return EventDecoder.decode_kafka_message(message_value, encoding)
