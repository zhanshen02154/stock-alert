# 注册工具
# 非必要请勿更改本文件
from typing import Any

from src.tools import (
    query_inventory,
    query_sales_volume,
    query_suppliers,
    search_smart_procurement_rules,
    restock_apply,
)
from src.tools.query_inventory import query_daily_sales_volume


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
            cls.tool_groups = {
                "tools_supply_chain": [
                    query_inventory,
                    query_sales_volume,
                    query_daily_sales_volume,
                    query_suppliers,
                    restock_apply,
                ],
                "tools_knowledges": [search_smart_procurement_rules],
            }

    @classmethod
    def get_tools_by_group(cls, group: str):
        if group in cls.tool_groups:
            return cls.tool_groups[group]

        return []
