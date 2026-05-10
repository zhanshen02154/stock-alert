# 注册工具
# 非必要请勿更改本文件
from typing import Any

from src.tools import query_inventory


class ToolRegistry:
    tool_groups: dict[str, Any] | None = {}

    @classmethod
    def init_tools(cls):
        cls._load_tool_groups()

    @classmethod
    def cleanup(cls):
        if cls.tool_groups:
            cls.tool_groups.clear()
            cls.tool_groups = None

    @classmethod
    def _load_tool_groups(cls):
        if not cls.tool_groups:
            cls.tool_groups = {"tools_data_query": [query_inventory]}

    @classmethod
    def get_tools_by_group(cls, group: str):
        if group in cls.tool_groups:
            return cls.tool_groups[group]

        return []
