import os

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.base_tool import ToolResult, BaseToolInput
from src.utils.api_client import HttpClient

# 全局配置
MICROSERVICE_URL = os.getenv("MICROSERVICE_URL", "") + "/api/v1"


class QueryInventoryInput(BaseToolInput):
    """检查库存输入参数"""

    sku_id: str = Field(description="商品SKU编号必须要SKU开头", pattern=r"^SKU")


class QueryInventoryOutput(BaseModel):
    """检查库存输出参数"""

    sku_id: str = Field(default="", description="商品SKU编号")
    name: str = Field(default="", description="商品SKU名称")
    stock: int = Field(default=0, description="商品当前库存")
    status: int = Field(
        default=0, description="商品状态（1上架 0下架），引用该数据时不展示数值"
    )
    stock_warn: int = Field(default=0, description="商品库存预警值")


@tool(description="查询单个商品的库存信息")
def query_inventory(sku_id: str) -> ToolResult:
    """
    查询单个商品的库存信息

    Args:
        sku_id: 商品SKU编号必须要SKU开头
    """
    if not sku_id.startswith("SKU"):
        return ToolResult(status="failed", data=None, error="sku_id必须以SKU开头")

    url = f"{MICROSERVICE_URL}/inventory/sku?sku_id={sku_id}"
    resp = HttpClient.get_sync_client().get(url=url, timeout=5)
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=QueryInventoryOutput(**data), error=None)
