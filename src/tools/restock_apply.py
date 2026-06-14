from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from src.core.schemas import Context
from src.tools.base_tool import ToolResult
from src.tools.query_inventory import MICROSERVICE_URL
from src.utils.api_client import HttpClient


# ========== 输出参数定义 ==========
class RestockRecord(BaseModel):
    """[输出参数] 补货申请成功后返回的记录数据"""

    id: int = Field(description="补货记录ID")
    sku_code: str = Field(description="商品编号")
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
    runtime: ToolRuntime[Context],
    sku_no: str,
    quantity: int = 1,
    reason: str = "",
    supplier_id: int = 0,
    supplier_name: str = "",
) -> ToolResult:
    """
    发起单个商品SKU的补货申请

    Args:
        sku_no: 商品SKU编号必须要SKU开头
        quantity: 补货数量
        reason: 补货原因
        supplier_id: 供应商ID
        supplier_name: 供应商名称
    """
    if not sku_no.startswith("SKU"):
        return ToolResult(status="failed", data=None, error="sku_no必须以SKU开头")

    url = f"{MICROSERVICE_URL}/inventory/restock"
    client = HttpClient.get_sync_client()
    response = interrupt(
        {
            "action": "restock_apply",
            "payload": {
                "sku_code": sku_no,
                "quantity": quantity,
                "reason": reason,
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
            },
            "message": f"是否发起针对{sku_no}的补货申请？补货数量:{quantity} 供应商:{supplier_name}",
        }
    )

    if response["action"] == "yes":
        with client.post(
            url=url,
            timeout=10,
            data={
                "sku_code": sku_no,
                "quantity": quantity,
                "reason": reason,
                "supplier_id": supplier_id,
                "user_id": runtime.context.user_id,
            },
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status_code != 200:
                return ToolResult(status="failed", data=None, error=resp.text)
            data = resp.json()
            return ToolResult(
                status="success", data=RestockApplyOutput(**data), error=None
            )
    else:
        return ToolResult(status="canceled", data=None, error=None)
