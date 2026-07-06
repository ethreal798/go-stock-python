"""股票相关模型"""

from sqlalchemy import Column, BigInteger, String, Float, DateTime, Integer, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from .base import Base, GormBaseModel, TimestampMixin, SoftDeleteMixin


class FollowedStock(Base):
    """关注股票"""

    __tablename__ = "followed_stock"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, nullable=True, comment="用户ID")
    stock_code = Column(String(20), index=True, name="stock_code")
    name = Column(String(50))
    volume = Column(BigInteger)
    cost_price = Column(Float, name="cost_price")
    price = Column(Float)
    price_change = Column(Float, name="price_change")
    change_percent = Column(Float, name="change_percent")
    alarm_change_percent = Column(Float, name="alarm_change_percent")
    alarm_price = Column(Float, name="alarm_price")
    time = Column(DateTime)
    sort = Column(BigInteger)
    cron = Column(String(255), nullable=True)
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")
    ai_config_id = Column(Integer, name="ai_config_id")
    entry_price = Column(Float, name="entry_price")
    take_profit_price = Column(Float, name="take_profit_price")
    stop_loss_price = Column(Float, name="stop_loss_price")

    groups = relationship(
        "StockGroupItem",
        back_populates="stock",
        primaryjoin="FollowedStock.stock_code == StockGroupItem.stock_code",
        foreign_keys="StockGroupItem.stock_code",
    )


class StockBasic(GormBaseModel):
    """股票基础信息"""

    __tablename__ = "stock_basics"

    ts_code = Column(String(50), index=True, name="ts_code")
    symbol = Column(String(20), index=True)
    name = Column(String(50), index=True)
    area = Column(String(50))
    industry = Column(String(50), index=True)
    fullname = Column(String(100))
    ename = Column(String(100))
    cnspell = Column(String(50))
    market = Column(String(20))
    exchange = Column(String(20))
    curr_type = Column(String(20), name="curr_type")
    list_status = Column(String(10), name="list_status")
    list_date = Column(String(20), name="list_date")
    delist_date = Column(String(20), name="delist_date")
    is_hs = Column(String(10), name="is_hs")
    act_name = Column(String(100), name="act_name")
    act_ent_type = Column(String(50), name="act_ent_type")
    bk_name = Column(String(100), name="bk_name")
    bk_code = Column(String(50), name="bk_code")


class AllStockInfo(GormBaseModel):
    """全量股票信息"""

    __tablename__ = "all_stock_info"

    secucode = Column(String(50), index=True, name="secucode")
    securitycode = Column(String(20), index=True, name="securitycode")
    securitynameabbr = Column(String(50), index=True, name="securitynameabbr")
    newprice = Column(String(20), name="newprice")
    changerate = Column(String(20), name="changerate")
    volumeratio = Column(String(20), name="volumeratio")
    highprice = Column(String(20), name="highprice")
    lowprice = Column(String(20), name="lowprice")
    precloseprice = Column(String(20), name="precloseprice")
    volume = Column(String(30), name="volume")
    dealamount = Column(String(30), name="dealamount")
    turnoverrate = Column(String(20), name="turnoverrate")
    market = Column(String(20), index=True)
    concept = Column(String(500), index=True)
    industry = Column(String(100), index=True)
    maxtradedate = Column(String(20), index=True, name="maxtradedate")


class StockInfoHK(GormBaseModel):
    """港股基础信息"""

    __tablename__ = "stock_base_info_hk"

    code = Column(String(20), index=True)
    name = Column(String(50))
    full_name = Column(String(100), name="full_name")
    e_name = Column(String(100), name="e_name")
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")
    bk_name = Column(String(100), name="bk_name")
    bk_code = Column(String(50), name="bk_code")


class StockInfoUS(GormBaseModel):
    """美股基础信息"""

    __tablename__ = "stock_base_info_us"

    code = Column(String(20), index=True)
    name = Column(String(50))
    full_name = Column(String(100), name="full_name")
    e_name = Column(String(100), name="e_name")
    exchange = Column(String(20))
    type = Column(String(20))
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")
    bk_name = Column(String(100), name="bk_name")
    bk_code = Column(String(50), name="bk_code")


class StockGroup(GormBaseModel):
    """股票分组"""

    __tablename__ = "stock_groups"

    user_id = Column(String(100), index=True, nullable=True, comment="所属用户ID")
    name = Column(String(100), index=True, comment="分组名称")
    sort = Column(Integer, default=0, comment="排序序号")

    items = relationship("StockGroupItem", back_populates="group", cascade="all, delete-orphan")


class StockGroupItem(GormBaseModel):
    """股票分组项"""

    __tablename__ = "group_stock_info"

    stock_code = Column(String(20), index=True, name="stock_code", comment="股票代码")
    group_id = Column(BigInteger, ForeignKey("stock_groups.id"), index=True, name="group_id", comment="分组ID")

    group = relationship("StockGroup", back_populates="items")
    stock = relationship(
        "FollowedStock",
        back_populates="groups",
        primaryjoin="StockGroupItem.stock_code == FollowedStock.stock_code",
        foreign_keys=[stock_code],
        uselist=False,
    )


class StockInfo(GormBaseModel):
    """实时股票信息"""

    __tablename__ = "stock_infos"

    date = Column(String(20), index=True)
    time = Column(String(20), index=True)
    code = Column(String(20), index=True)
    name = Column(String(50), index=True)
    pre_price = Column(Float, name="pre_price")
    price = Column(String(20))
    volume = Column(String(30))
    amount = Column(String(30))
    open = Column(String(20))
    pre_close = Column(String(20), name="pre_close")
    high = Column(String(20))
    low = Column(String(20))
    bid = Column(String(20))
    ask = Column(String(20))
    b1p = Column(String(20), name="b1p")
    b1v = Column(String(20), name="b1v")
    b2p = Column(String(20), name="b2p")
    b2v = Column(String(20), name="b2v")
    b3p = Column(String(20), name="b3p")
    b3v = Column(String(20), name="b3v")
    b4p = Column(String(20), name="b4p")
    b4v = Column(String(20), name="b4v")
    b5p = Column(String(20), name="b5p")
    b5v = Column(String(20), name="b5v")
    a1p = Column(String(20), name="a1p")
    a1v = Column(String(20), name="a1v")
    a2p = Column(String(20), name="a2p")
    a2v = Column(String(20), name="a2v")
    a3p = Column(String(20), name="a3p")
    a3v = Column(String(20), name="a3v")
    a4p = Column(String(20), name="a4p")
    a4v = Column(String(20), name="a4v")
    a5p = Column(String(20), name="a5p")
    a5v = Column(String(20), name="a5v")


class IndexBasic(GormBaseModel):
    """指数基础信息"""

    __tablename__ = "tushare_index_basic"

    ts_code = Column(String(50), index=True, name="ts_code")
    symbol = Column(String(20), index=True)
    name = Column(String(50), index=True)
    full_name = Column(String(100), name="full_name")
    index_type = Column(String(50), name="index_type")
    category = Column(String(50))
    market = Column(String(20))
    list_date = Column(String(20), name="list_date")
    base_date = Column(String(20), name="base_date")
    base_point = Column(Float, name="base_point")
    publisher = Column(String(100))
    weight_rule = Column(String(50), name="weight_rule")
    desc = Column(Text)


class TradingRecord(Base, TimestampMixin):
    """交易记录"""

    __tablename__ = "trading_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, nullable=True, comment="所属用户ID")
    stock_code = Column(String(20), index=True, name="stock_code", comment="股票代码")
    stock_name = Column(String(50), name="stock_name", comment="股票名称")
    direction = Column(String(10), index=True, comment="交易方向: buy/sell")
    price = Column(Float, comment="成交价格")
    volume = Column(BigInteger, comment="成交数量")
    reason = Column(Text, comment="买入/卖出理由")
    stop_loss_price = Column(Float, name="stop_loss_price", comment="预设止损价")
    take_profit_price = Column(Float, name="take_profit_price", comment="预设止盈价")
    fee = Column(Float, comment="交易手续费")
    market_value = Column(Float, name="market_value", comment="市值/金额")
    mindset = Column(Text, comment="交易心态记录")
    recorded_close_price = Column(Float, name="recorded_close_price", comment="记录时的收盘价")
    trading_time = Column(DateTime, index=True, name="trading_time", comment="交易成交时间")


class BKDict(GormBaseModel):
    """板块字典"""

    __tablename__ = "bk_dict"

    bk_code = Column(String(50), name="bk_code")
    bk_name = Column(String(100), name="bk_name")
    first_letter = Column(String(50), name="first_letter")
    fubk_code = Column(String(50), name="fubk_code")
    publish_code = Column(String(50), name="publish_code")
