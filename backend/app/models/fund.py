"""基金相关模型。"""

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from .base import GormBaseModel


class Fund(GormBaseModel):
    """基金基础信息"""

    __tablename__ = "funds"

    code = Column(String(20), unique=True, index=True, nullable=False, comment="基金代码")
    name = Column(String(200), index=True, nullable=False, comment="基金名称")
    type = Column(String(50), index=True, comment="基金类型")
    category = Column(String(20), index=True, nullable=False, default="unknown", comment="数据路由分类")
    status = Column(String(20), index=True, nullable=False, default="unknown", comment="排行可观测状态")
    last_seen_data_date = Column(Date, index=True, comment="最近一次在排行中出现的数据日期")
    last_seen_at = Column(DateTime, comment="最近一次在排行中出现的抓取时间")


class FollowedFund(GormBaseModel):
    """关注基金"""

    __tablename__ = "followed_funds"

    user_id = Column(BigInteger, index=True, comment="用户ID")
    fund_code = Column(String(20), index=True, nullable=False, comment="基金代码")
    remark = Column(String(200), comment="备注")


class FundOpenRankLatest(GormBaseModel):
    """开放式基金最新排行；LOF 按东方财富口径归入本表。"""

    __tablename__ = "fund_open_rank_latest"

    fund_id = Column(BigInteger, ForeignKey("funds.id"), unique=True, index=True, nullable=False)
    fund_code = Column(String(20), unique=True, index=True, nullable=False, comment="基金代码")
    fund_name = Column(String(200), nullable=False, comment="来源基金简称")
    data_date = Column(Date, index=True, comment="净值日期；尚未披露时为空")
    unit_nav = Column(Numeric(18, 8), comment="单位净值")
    accumulated_nav = Column(Numeric(18, 8), comment="累计净值")
    daily_growth_pct = Column(Numeric(12, 6), comment="日增长率(%)")
    return_1w_pct = Column(Numeric(12, 6), comment="近1周收益率(%)")
    return_1m_pct = Column(Numeric(12, 6), comment="近1月收益率(%)")
    return_3m_pct = Column(Numeric(12, 6), comment="近3月收益率(%)")
    return_6m_pct = Column(Numeric(12, 6), comment="近6月收益率(%)")
    return_1y_pct = Column(Numeric(12, 6), comment="近1年收益率(%)")
    return_2y_pct = Column(Numeric(12, 6), comment="近2年收益率(%)")
    return_3y_pct = Column(Numeric(12, 6), comment="近3年收益率(%)")
    return_ytd_pct = Column(Numeric(12, 6), comment="今年以来收益率(%)")
    return_since_inception_pct = Column(Numeric(12, 6), comment="成立以来收益率(%)")
    fetched_at = Column(DateTime, nullable=False, comment="抓取时间")


class FundExchangeRankLatest(GormBaseModel):
    """场内交易基金最新排行。"""

    __tablename__ = "fund_exchange_rank_latest"

    fund_id = Column(BigInteger, ForeignKey("funds.id"), unique=True, index=True, nullable=False)
    fund_code = Column(String(20), unique=True, index=True, nullable=False, comment="基金代码")
    fund_name = Column(String(200), nullable=False, comment="来源基金简称")
    fund_type = Column(String(50), comment="东方财富场内基金类型")
    data_date = Column(Date, index=True, comment="净值日期；尚未披露时为空")
    unit_nav = Column(Numeric(18, 8), comment="单位净值")
    accumulated_nav = Column(Numeric(18, 8), comment="累计净值")
    return_1w_pct = Column(Numeric(12, 6), comment="近1周收益率(%)")
    return_1m_pct = Column(Numeric(12, 6), comment="近1月收益率(%)")
    return_3m_pct = Column(Numeric(12, 6), comment="近3月收益率(%)")
    return_6m_pct = Column(Numeric(12, 6), comment="近6月收益率(%)")
    return_1y_pct = Column(Numeric(12, 6), comment="近1年收益率(%)")
    return_2y_pct = Column(Numeric(12, 6), comment="近2年收益率(%)")
    return_3y_pct = Column(Numeric(12, 6), comment="近3年收益率(%)")
    return_ytd_pct = Column(Numeric(12, 6), comment="今年以来收益率(%)")
    return_since_inception_pct = Column(Numeric(12, 6), comment="成立以来收益率(%)")
    inception_date = Column(Date, comment="成立日期")
    fetched_at = Column(DateTime, nullable=False, comment="抓取时间")


class FundMoneyRankLatest(GormBaseModel):
    """货币型基金最新排行。"""

    __tablename__ = "fund_money_rank_latest"

    fund_id = Column(BigInteger, ForeignKey("funds.id"), unique=True, index=True, nullable=False)
    fund_code = Column(String(20), unique=True, index=True, nullable=False, comment="基金代码")
    fund_name = Column(String(200), nullable=False, comment="来源基金简称")
    data_date = Column(Date, index=True, comment="收益日期；尚未披露时为空")
    income_per_10k = Column(Numeric(18, 8), comment="万份收益(元/万份，非百分比)")
    annualized_7d_pct = Column(Numeric(12, 6), comment="7日年化收益率(%)")
    annualized_14d_pct = Column(Numeric(12, 6), comment="14日年化收益率(%)")
    annualized_28d_pct = Column(Numeric(12, 6), comment="28日年化收益率(%)")
    return_1m_pct = Column(Numeric(12, 6), comment="近1月收益率(%)")
    return_3m_pct = Column(Numeric(12, 6), comment="近3月收益率(%)")
    return_6m_pct = Column(Numeric(12, 6), comment="近6月收益率(%)")
    return_1y_pct = Column(Numeric(12, 6), comment="近1年收益率(%)")
    return_2y_pct = Column(Numeric(12, 6), comment="近2年收益率(%)")
    return_3y_pct = Column(Numeric(12, 6), comment="近3年收益率(%)")
    return_5y_pct = Column(Numeric(12, 6), comment="近5年收益率(%)")
    return_ytd_pct = Column(Numeric(12, 6), comment="今年以来收益率(%)")
    return_since_inception_pct = Column(Numeric(12, 6), comment="成立以来收益率(%)")
    fetched_at = Column(DateTime, nullable=False, comment="抓取时间")


class FundOpenNavHistory(GormBaseModel):
    """开放式基金（含按开放式口径处理的 LOF）净值历史。"""

    __tablename__ = "fund_open_nav_history"
    __table_args__ = (UniqueConstraint("fund_id", "data_date", name="uq_fund_open_nav_history_fund_date"),)

    fund_id = Column(BigInteger, ForeignKey("funds.id"), nullable=False)
    fund_code = Column(String(20), nullable=False, comment="基金代码")
    data_date = Column(Date, nullable=False, index=True, comment="净值日期")
    unit_nav = Column(Numeric(18, 8), comment="单位净值")
    accumulated_nav = Column(Numeric(18, 8), comment="累计净值")
    daily_growth_pct = Column(Numeric(12, 6), comment="日增长率(%)")
    fetched_at = Column(DateTime, nullable=False, comment="抓取时间")


class FundMoneyYieldHistory(GormBaseModel):
    """货币基金收益历史。"""

    __tablename__ = "fund_money_yield_history"
    __table_args__ = (UniqueConstraint("fund_id", "data_date", name="uq_fund_money_yield_history_fund_date"),)

    fund_id = Column(BigInteger, ForeignKey("funds.id"), nullable=False)
    fund_code = Column(String(20), nullable=False, comment="基金代码")
    data_date = Column(Date, nullable=False, index=True, comment="收益日期")
    income_per_10k = Column(Numeric(18, 8), comment="每万份收益（元）")
    annualized_7d_pct = Column(Numeric(12, 6), comment="七日年化收益率(%)")
    purchase_status = Column(String(50), comment="申购状态")
    redemption_status = Column(String(50), comment="赎回状态")
    fetched_at = Column(DateTime, nullable=False, comment="抓取时间")
