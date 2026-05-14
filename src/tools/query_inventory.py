import os

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.base_tool import ToolResult, BaseToolInput
from src.utils.api_client import HttpClient

# 全局配置
MICROSERVICE_URL = os.getenv("MICROSERVICE_URL", "") + "/api/v1"


class QueryInventoryInput(BaseToolInput):
    """检查库存输入参数"""

    sku_code: str = Field(description="商品SKU编号必须要SKU开头", pattern=r"^SKU")


class QueryInventoryOutput(BaseModel):
    """检查库存输出参数"""

    sku_code: str = Field(default="", description="商品SKU的编号（SKU开头）")
    name: str = Field(default="", description="商品SKU名称")
    stock: int = Field(default=0, description="商品当前库存")
    status: int = Field(
        default=0, description="商品状态（1上架 0下架），引用该数据时不展示数值"
    )
    stock_warn: int = Field(default=0, description="商品库存预警值")


class QuerySalesVolumeInput(BaseToolInput):
    """查询销量输入参数"""

    sku_code: str = Field(description="商品SKU编号", pattern=r"^SKU")
    start_time: str = Field(description="开始时间，格式：YYYY-MM-DD HH:MM:SS")
    end_time: str = Field(description="结束时间，格式：YYYY-MM-DD HH:MM:SS")


class QuerySalesVolumeOutput(BaseModel):
    """查询销量输出参数"""

    sales_volume: int = Field(default=0, description="累计销量")
    sku_code: str = Field(default="", description="SKU编号")
    daily_avg_sales: float = Field(default=0.0, description="日均销量")


class SupplierInfo(BaseModel):
    """供应商信息"""

    id: int = Field(default=0, description="供应商ID")
    name: str = Field(default="", description="供应商名称")
    contact_person: str = Field(default="", description="联系人")
    phone: str = Field(default="", description="联系电话")
    email: str = Field(default="", description="电子邮件")
    address: str = Field(default="", description="地址")
    rating: float = Field(default=0.0, description="供应商评级")
    lead_time_days: int = Field(default=0, description="交货周期（天）")
    payment_terms: str = Field(default="", description="支付条款")


class SupplierProductInfo(BaseModel):
    """供应商商品关联信息"""

    supplier: SupplierInfo = Field(description="供应商信息")
    supply_price: float = Field(default=0.0, description="供应价")
    min_order_quantity: int = Field(default=0, description="起订数量")
    is_preferred: bool = Field(default=False, description="是否首选")
    sku_code: str = Field(default="", description="SKU编码")
    supplier_id: int = Field(default=0, description="供应商ID")


class QuerySuppliersOutput(BaseModel):
    """查询供应商列表输出参数"""

    suppliers: list[SupplierProductInfo] = Field(default=[], description="供应商列表")


class DailySalesVolumeItem(BaseModel):
    """商品每日销量列表项"""

    date: str = Field(default="", description="日期")
    sales_volume: int = Field(default=0, description="销量")
    sku_code: str = Field(default="", description="SKU编号")


class DailySalesList(BaseModel):
    """
    商品每日销量列表
    """

    daily_sales: list[DailySalesVolumeItem] = Field(
        default=[], description="商品每日销量列表项"
    )


@tool(description="查询单个商品SKU的库存信息")
def query_inventory(sku_code: str) -> ToolResult:
    """
    查询单个商品的库存信息

    Args:
        sku_code: 商品SKU编号必须要SKU开头
    """
    if not sku_code.startswith("SKU"):
        return ToolResult(status="failed", data=None, error="sku_code必须以SKU开头")

    url = f"{MICROSERVICE_URL}/inventory/sku"
    resp = HttpClient.get_sync_client().get(
        url=url, timeout=5, params={"sku_code": sku_code}
    )
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=QueryInventoryOutput(**data), error=None)


@tool(
    description="获取商品指定时间段内的总销量和日均销量",
    args_schema=QuerySalesVolumeInput,
)
def query_sales_volume(sku_code: str, start_time: str, end_time: str) -> ToolResult:
    """
    获取指定商品SKU在指定时间区间的总销量和日均销量

    Args:
        sku_code: 商品SKU编号
        start_time: 开始时间，格式：YYYY-MM-DD
        end_time: 结束时间，格式：YYYY-MM-DD
    """

    url = f"{MICROSERVICE_URL}/product/sales_volume"
    params = {
        "sku_code": sku_code,
        "start_time": start_time + " 00:00:00",
        "end_time": end_time + " 23:59:59",
    }
    resp = HttpClient.get_sync_client().get(url=url, params=params, timeout=5)
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=QuerySalesVolumeOutput(**data), error=None)


@tool(description="通过sku的编号获取对应的供应商列表")
def query_suppliers(sku_code: str) -> ToolResult:
    """
    通过sku_code获取对应的供应商列表

    Args:
        sku_code: 商品SKU编号
    """

    url = f"{MICROSERVICE_URL}/supplier"
    params = {
        "sku_code": sku_code,
    }
    resp = HttpClient.get_sync_client().get(url=url, params=params, timeout=5)
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=QuerySuppliersOutput(**data), error=None)


@tool(description="通过sku的编号获取指定时间区间的每日销量数据")
def query_daily_sales_volume(
    sku_code: str, start_date: str, end_date: str
) -> ToolResult:
    """
    通过sku的编号获取指定时间区间的历史销量数据

    Args:
        sku_code: 商品SKU编号
        start_date: 起始日期 格式: YYYY-MM-DD
        end_date: 截止日期 格式: YYYY-MM-DD
    """

    url = f"{MICROSERVICE_URL}/inventory/daily_sales_volume"
    params = {
        "sku_code": sku_code,
        "start_date": start_date,
        "end_date": end_date,
    }
    resp = HttpClient.get_sync_client().get(url=url, params=params, timeout=5)
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=DailySalesList(**data), error=None)
