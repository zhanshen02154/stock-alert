"""
会话存储模块 - MySQL实现
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SessionStore(ABC):
    """会话存储抽象基类"""
    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """初始化"""
        pass
