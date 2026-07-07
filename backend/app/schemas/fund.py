"""基金相关 Pydantic Schema。"""

from datetime import datetime
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
    nav: Optional[float] = Field(None, description="单位净值")
    acc_nav: Optional[float] = Field(None, description="累计净值")
    day_growth: Optional[float] = Field(None, description="日增长率(%)")
    week_growth: Optional[float] = Field(None, description="近一周增长率(%)")
    month_growth: Optional[float] = Field(None, description="近一月增长率(%)")
    three_month_growth: Optional[float] = Field(None, description="近三月增长率(%)")
    six_month_growth: Optional[float] = Field(None, description="近六月增长率(%)")
    year_growth: Optional[float] = Field(None, description="近一年增长率(%)")
    current_year_growth: Optional[float] = Field(None, description="今年以来增长率(%)")
    manager: Optional[str] = Field(None, description="基金经理")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")

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
    hold_units: float
    cost_price: float

    # 嵌套基金基础信息
    fund_info: Optional[FundResponse] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
