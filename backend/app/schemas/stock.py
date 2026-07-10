"""股票相关 Pydantic Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ============================================================
# 基础模型
# ============================================================


class StockBase(BaseModel):
    """股票基础信息。"""

    code: str = Field(..., description="股票代码，如 600519")
    name: str = Field(..., description="股票名称，如 贵州茅台")
    market: Optional[str] = Field(None, description="市场：sh / sz / bj")


class StockCreate(StockBase):
    """创建股票关注请求。"""

    group_name: Optional[str] = Field(None, description="分组名称")
    remark: Optional[str] = Field(None, description="备注")


class StockResponse(StockBase):
    """股票信息响应。"""

    id: int
    group_name: Optional[str] = None
    remark: Optional[str] = None
    is_followed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ============================================================
# 实时行情
# ============================================================


class StockRealTimePrice(BaseModel):
    """股票实时行情。"""

    code: str = Field(..., description="股票代码")
    name: str = Field("", description="股票名称")
    current_price: Optional[float] = Field(None, description="当前价格")
    change_percent: Optional[float] = Field(None, description="涨跌幅(%)")
    change_amount: Optional[float] = Field(None, description="涨跌额")
    open_price: Optional[float] = Field(None, description="开盘价")
    high_price: Optional[float] = Field(None, description="最高价")
    low_price: Optional[float] = Field(None, description="最低价")
    prev_close: Optional[float] = Field(None, description="昨收价")
    volume: Optional[int] = Field(None, description="成交量(手)")
    amount: Optional[float] = Field(None, description="成交额(元)")
    turnover_rate: Optional[float] = Field(None, description="换手率(%)")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    total_market_cap: Optional[float] = Field(None, description="总市值")
    circulating_market_cap: Optional[float] = Field(None, description="流通市值")
    timestamp: Optional[datetime] = Field(None, description="数据时间戳")


# ============================================================
# 搜索
# ============================================================


class StockSearchResult(BaseModel):
    """股票搜索结果。"""

    code: str
    name: str
    market: Optional[str] = None
    pinyin: Optional[str] = None


# ============================================================
# K线
# ============================================================


class KlineRequest(BaseModel):
    """K线数据请求。"""

    code: str = Field(..., description="股票代码")
    source: str = Field("eastmoney", description="数据源: eastmoney / sina / tdx")
    period: str = Field("daily", description="周期: daily / weekly / monthly / 60min / 30min / 15min / 5min")
    count: int = Field(120, description="返回数据条数", ge=1, le=1000)
