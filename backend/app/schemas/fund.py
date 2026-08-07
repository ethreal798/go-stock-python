"""基金相关 Pydantic Schema。"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

# ============================================================
# 基金基础信息
# ============================================================


class FundBase(BaseModel):
    """基金基础信息。"""

    code: str = Field(..., description="基金代码")
    name: str = Field(..., description="基金名称")
    type: Optional[str] = Field(None, description="基金类型")


class FundResponse(FundBase):
    """基金详细信息响应。"""

    id: int
    category: str = Field("unknown", description="数据路由分类")
    status: str = Field("unknown", description="排行可观测状态")
    last_seen_data_date: Optional[date] = Field(None, description="最近一次排行数据日期")
    last_seen_at: Optional[datetime] = Field(None, description="最近一次排行抓取时间")
    is_followed: Optional[bool] = Field(False, description="是否已关注")

    model_config = {"from_attributes": True}


# ============================================================
# 关注基金
# ============================================================


class FollowedFundCreate(BaseModel):
    """关注基金请求。"""

    fund_code: str = Field(..., description="基金代码")
    remark: Optional[str] = Field(None, description="备注")


class FollowedFundResponse(BaseModel):
    """关注基金响应。"""

    id: int
    user_id: int
    fund_code: str
    remark: Optional[str] = None

    # 嵌套基金基础信息
    fund_info: Optional[FundResponse] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
