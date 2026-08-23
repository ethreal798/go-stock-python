"""基金相关 Pydantic Schema。"""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

FundTrendPeriod = Literal["1m", "3m", "6m", "1y", "3y", "5y", "ytd", "since_inception"]

# ============================================================
# 基金基础信息
# ============================================================


class FundBase(BaseModel):
    """基金基础信息。"""
    id: int = Field(..., description="基金主表对应id")
    code: str = Field(..., description="基金代码")
    name: str = Field(..., description="基金名称")
    fund_type: str = Field(..., description="基金类型")
    is_hb: bool = Field(..., description="是否为货币基金")
    is_exchange: bool = Field(..., description="是否为场内基金")


class FundLatestResponse(BaseModel):
    """三个排行表的统一最新指标外壳。不同口径的字段按需返回。"""

    data_date: Optional[date] = None
    unit_nav: Optional[float] = None
    accumulated_nav: Optional[float] = None
    daily_growth_pct: Optional[float] = None
    return_1w_pct: Optional[float] = None
    return_1m_pct: Optional[float] = None
    return_3m_pct: Optional[float] = None
    return_6m_pct: Optional[float] = None
    return_1y_pct: Optional[float] = None
    return_2y_pct: Optional[float] = None
    return_3y_pct: Optional[float] = None
    return_5y_pct: Optional[float] = None
    return_ytd_pct: Optional[float] = None
    return_since_inception_pct: Optional[float] = None
    income_per_10k: Optional[float] = None
    annualized_7d_pct: Optional[float] = None
    annualized_14d_pct: Optional[float] = None
    annualized_28d_pct: Optional[float] = None


class FundResponse(FundBase):
    """基金详细信息响应。"""

    latest: Optional[FundLatestResponse] = Field(None, description="对应分类的最新排行指标")
    is_in_watchlist: Optional[bool] = Field(False, description="是否已加入自选")


class FundPerformanceTrendSeriesResponse(BaseModel):
    """一条累计收益率曲线。"""

    key: str
    name: str
    latest_return_pct: Optional[float] = None
    points: list[tuple[str, Optional[float]]]


class FundPerformanceTrendResponse(BaseModel):
    """指定基金和周期的最新累计收益率绘图快照。"""

    fund_code: str
    is_hb: bool
    period: FundTrendPeriod
    start_date: date
    end_date: date
    fetched_at: datetime
    is_stale: bool
    series: list[FundPerformanceTrendSeriesResponse]


# ============================================================
# 基金自选
# ============================================================


class FundWatchlistItemCreate(BaseModel):
    """加入基金自选请求。"""

    fund_code: str = Field(..., description="基金代码")
    remark: Optional[str] = Field(None, description="备注")


class FundWatchlistItemResponse(BaseModel):
    """基金自选项响应。"""

    id: int
    user_id: int
    remark: Optional[str] = None

    # 嵌套基金基础信息
    fund_info: Optional[FundResponse] = None

    created_at: datetime
    updated_at: datetime


class FundWatchlistRequest(BaseModel):
    """入参"""

    category: str  # 货币  开放  场内
    fund_type: str  # 基金类型 比如 指数型股票


# ============================================================
# 基金排行
# ============================================================

FundRankCategory = Literal["open", "money", "exchange"]

FundRankSortField = Literal[
    "nav",
    "accumulated_nav",
    "1w",
    "1m",
    "3m",
    "6m",
    "1y",
    "2y",
    "3y",
    "5y",
    "ytd",
    "since_inception",
    "income_per_10k",
    "annualized_7d",
    "annualized_14d",
    "annualized_28d",
]

FundRankPeriod = Literal[
    "1w",
    "1m",
    "3m",
    "6m",
    "1y",
    "2y",
    "3y",
    "5y",
    "ytd",
    "since_inception",
]

FundRankOrder = Literal["asc", "desc"]


class FundRankItemResponse(BaseModel):
    """排行列表中单条基金的响应。"""

    code: str = Field(..., description="基金代码")
    name: str = Field(..., description="基金名称")
    type: Optional[str] = Field(None, description="基金类型")
    category: str = Field(..., description="数据分类: open/money/exchange")
    data_date: Optional[date] = Field(None, description="净值/收益日期")

    # 完整最新指标（复用现有 schema）
    latest: Optional[FundLatestResponse] = Field(None, description="基金最新指标")

    # 自选状态
    is_in_watchlist: bool = Field(False, description="是否已加入自选")

    model_config = {"from_attributes": True}


class FundRankListResponse(BaseModel):
    """基金排行分页响应。"""

    items: list[FundRankItemResponse] = Field(..., description="排行列表")
    total: int = Field(..., description="符合条件的总记录数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    category: str = Field(..., description="基金分类")
    sort: str = Field(..., description="排序字段")
    period: str = Field(..., description="显示周期")
    order: str = Field(..., description="排序方向: asc/desc")
