import os
from typing import Any
import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.tools.base_tool import BaseToolInput, ToolResult
from src.tools.registry import tool_registry


class QueryInventoryInput(BaseToolInput):
    """检查库存输入参数"""
    sku_id: str = Field(description="商品SKU ID必须要SKU开头", pattern=r"^SKU")

class QueryInventoryOutput(BaseModel):
    """检查库存输出参数"""
    sku_id: str = Field(default="", description="商品SKU ID")
    name: str = Field(default="", description="商品SKU名称")
    stock: int = Field(default=0, description="商品当前库存")
    status: int = Field(default=0, description="商品状态（1上架 0下架），引用该数据时不展示数值")
    stock_warn: int = Field(default=0, description="商品库存预警值")

class QueryInventory(BaseTool):
    name: str = "query_inventory"
    description: str = "查询单个商品的库存信息"
    args_schema: type[BaseModel] = QueryInventoryInput
    http_client: requests.Session = None
    base_url: str = ""
    timeout: int = 5

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.http_client = requests.Session()
        self.base_url = os.getenv("MICROSERVICE_URL") + "/api/v1"
        self.timeout = 5

    def _run(self, *args: Any, **kwargs: Any) -> ToolResult:
        params = QueryInventoryInput(**kwargs)
        url = f"{self.base_url}/inventory/sku?sku_id={params.sku_id}"
        resp = self.http_client.get(url=url, timeout=self.timeout)
        if resp.status_code != 200:
            return ToolResult(status="failed", data=None, error=resp.text)
        data = resp.json()
        QueryInventoryOutput()
        return ToolResult(status="success", data=QueryInventoryOutput(**data), error=None)

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("async version not implemented")




