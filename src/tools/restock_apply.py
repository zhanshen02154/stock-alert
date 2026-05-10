from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.base_tool import ToolResult
from src.tools.query_inventory import MICROSERVICE_URL
from src.utils.api_client import HttpClient


# ========== 输出参数定义 ==========
class RestockRecord(BaseModel):
    """[输出参数] 补货申请成功后返回的记录数据"""

    id: int = Field(description="补货记录ID")
    sku_id: int = Field(description="商品SKU ID")
    user_id: int = Field(description="用户ID（该数据禁止展示）")
    quantity: int = Field(description="补货数量")
    reason: str = Field(description="补货原因")
    status: int = Field(
        description="补货状态（补货状态：1=待订货 2=部分订货 3=已订货 4=失败）"
    )
    created_at: str = Field(description="创建时间")


class SkuBasicInfo(BaseModel):
    """[输出参数] 补货申请关联的商品SKU信息"""

    id: int = Field(description="商品SKU ID")
    sku_name: str = Field(description="商品SKU名称")
    sku_no: str = Field(description="商品SKU编号")


class RestockApplyOutput(BaseModel):
    """[输出参数] 发起补货申请的响应结果"""

    restock_record: RestockRecord = Field(description="补货记录")
    sku_info: SkuBasicInfo = Field(description="商品基本信息")


@tool(description="发起单个商品SKU的补货申请")
def restock_apply(
    sku_id: str, quantity: int = 1, reason: str = "", user_id: int = -1
) -> ToolResult:
    """
    发起单个商品SKU的补货申请

    Args:
        sku_id: 商品SKU ID必须要SKU开头
        quantity: 补货数量
        reason: 补货原因
        user_id: 用户ID，当前系统一律为-1，禁止暴露
    """
    if not sku_id.startswith("SKU"):
        return ToolResult(status="failed", data=None, error="sku_id必须以SKU开头")

    url = f"{MICROSERVICE_URL}/inventory/restock"
    resp = HttpClient.get_sync_client().post(
        url=url,
        timeout=5,
        data={
            "sku_id": sku_id,
            "quantity": quantity,
            "reason": reason,
            "user_id": user_id,
        },
        headers={"Content-Type": "application/json"},
    )
    if resp.status_code != 200:
        return ToolResult(status="failed", data=None, error=resp.text)
    data = resp.json()
    resp.close()
    return ToolResult(status="success", data=RestockApplyOutput(**data), error=None)
