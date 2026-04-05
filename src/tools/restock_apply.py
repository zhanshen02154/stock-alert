import os
from typing import Any
import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.tools.base_tool import BaseToolInput, ToolResult, ToolStatus
from src.tools.registry import tool_registry
from src.utils.api_client import ApiClientManager


# ========== 输入参数定义 ==========

class RestockApplyInput(BaseToolInput):
    """[输入参数] 发起补货申请时需要提供的参数"""
    sku_id: str = Field(description="商品SKU ID必须要SKU开头", pattern=r"^SKU")
    user_id: int = Field(description="用户ID，当前系统一律为-1，禁止暴露", default=-1)
    quantity: int = Field(description="补货数量", default=1)
    reason: str = Field(description="补货原因", default="")


# ========== 输出参数定义（以下类仅供输出使用，不可作为工具输入参数） ==========

class RestockRecord(BaseModel):
    """[输出参数] 补货申请成功后返回的记录数据"""
    id: int = Field(description="补货记录ID")
    sku_id: int = Field(description="商品SKU ID")
    user_id: int = Field(description="用户ID（该数据禁止展示）")
    quantity: int = Field(description="补货数量")
    reason: str = Field(description="补货原因")
    status: int = Field(description="补货状态（补货状态：1=待订货 2=部分订货 3=已订货 4=失败）")
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


@tool_registry.register(name="restock_apply", description="发起补货申请中...")
class RestockApply(BaseTool):
    name: str = "restock_apply"
    description: str = "发起单个商品SKU的补货申请"
    args_schema: type[BaseModel] = RestockApplyInput
    base_url: str = ""
    timeout: int = 5
    headers: dict[str, str] = {"Content-Type": "application/json"}

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.base_url = os.getenv("MICROSERVICE_URL") + "/api/v1"
        self.timeout = 5

    def _run(self, *args: Any, **kwargs: Any) -> ToolResult:
        params = RestockApplyInput(**kwargs)
        url = f"{self.base_url}/inventory/restock"
        resp = ApiClientManager.get_sync_client().post(url=url, timeout=self.timeout, data=params.model_dump(),
                                                       headers=self.headers)
        if resp.status_code != 200:
            return ToolResult(status="failed", data=None, error=resp.text)
        data = resp.json()
        resp.close()
        return ToolResult(status="success", data=RestockApplyOutput(**data), error=None)

    async def _arun(self, *args: Any, **kwargs: Any):
        params = RestockApplyInput(**kwargs)
        url = f"{self.base_url}/inventory/restock"
        resp = await ApiClientManager.get_async_client().post(url=url, timeout=self.timeout, data=params.model_dump(),
                                                              headers=self.headers)
        if resp.status_code != 200:
            return ToolResult(status="failed", data=None, error=resp.text)
        data = resp.json()
        await resp.aclose()
        return ToolResult(status="success", data=RestockApplyOutput(**data), error=None)
