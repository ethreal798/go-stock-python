"""基金相关模型"""

from sqlalchemy import Column, String, Float, DateTime, BigInteger, Index
from .base import GormBaseModel, Base, TimestampMixin


class Fund(GormBaseModel):
    """基金基础信息"""
    __tablename__ = "funds"

    code = Column(String(20), unique=True, index=True, nullable=False, comment="基金代码")
    name = Column(String(100), index=True, nullable=False, comment="基金名称")
    type = Column(String(50), index=True, comment="基金类型")
    nav = Column(Float, comment="单位净值")
    acc_nav = Column(Float, comment="累计净值")
    day_growth = Column(Float, comment="日增长率(%)")
    week_growth = Column(Float, comment="近一周增长率(%)")
    month_growth = Column(Float, comment="近一月增长率(%)")
    three_month_growth = Column(Float, comment="近三月增长率(%)")
    six_month_growth = Column(Float, comment="近六月增长率(%)")
    year_growth = Column(Float, comment="近一年增长率(%)")
    current_year_growth = Column(Float, comment="今年以来增长率(%)")
    manager = Column(String(100), comment="基金经理")
    last_update = Column(DateTime, comment="最后更新时间")


class FollowedFund(GormBaseModel):
    """关注基金"""
    __tablename__ = "followed_funds"

    user_id = Column(BigInteger, index=True, comment="用户ID")
    fund_code = Column(String(20), index=True, nullable=False, comment="基金代码")
    remark = Column(String(200), comment="备注")

    # 可以考虑增加持仓相关字段
    hold_units = Column(Float, default=0.0, comment="持有份额")
    cost_price = Column(Float, default=0.0, comment="持仓成本")
