from .base_handler import BaseHandler


class HandlerRegistry:
    """Handler 注册中心，用于管理和查找事件处理器"""
    
    def __init__(self):
        self._handlers: dict[str, BaseHandler] = {}
    
    def register(self, handler: BaseHandler) -> None:
        """
        注册事件处理器
        
        Args:
            handler: 处理器实例
        """
        event_type = handler.event_type
        if event_type in self._handlers:
            raise ValueError(f"事件类型 '{event_type}' 已有注册的处理器")
        self._handlers[event_type] = handler
    
    def get_handler(self, event_type: str) -> BaseHandler:
        """
        根据事件类型获取处理器
        
        Args:
            event_type: 事件类型
            
        Returns:
            对应的事件处理器
            
        Raises:
            KeyError: 如果没有找到对应的处理器
        """
        if event_type not in self._handlers:
            raise KeyError(f"未找到事件类型 '{event_type}' 的处理器")
        return self._handlers[event_type]
    
    def has_handler(self, event_type: str) -> bool:
        """检查是否存在指定事件类型的处理器"""
        return event_type in self._handlers
    
    def get_all_event_types(self) -> list[str]:
        """获取所有已注册的事件类型"""
        return list(self._handlers.keys())
    
    def clear(self) -> None:
        """清空所有注册的处理器"""
        self._handlers.clear()


# 全局注册中心实例
registry = HandlerRegistry()


def register_handler(handler: BaseHandler) -> None:
    """注册处理器的便捷函数"""
    registry.register(handler)


def get_handler(event_type: str) -> BaseHandler:
    """获取处理器的便捷函数"""
    return registry.get_handler(event_type)
