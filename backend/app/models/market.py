"""市场数据模型"""

from sqlalchemy import Column, BigInteger, String, Integer, Float, DateTime, Text, Index, func
from .base import Base, GormBaseModel


class MarketStatistic(Base):
    """全市场行情统计"""

    __tablename__ = "market_statistic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    data_date = Column(String(10), index=True, name="data_date", comment="日期(YYYY-MM-DD)")
    data_time = Column(String(8), index=True, name="data_time", comment="时间(HH:mm:ss)")
    up_count = Column(Integer, name="up_count", comment="上涨家数")
    down_count = Column(Integer, name="down_count", comment="下跌家数")
    up_ratio = Column(Float, name="up_ratio", comment="上涨占比")
    up_down_ratio = Column(Float, name="up_down_ratio", comment="涨跌比")
    sentiment_desc = Column(String(20), name="sentiment_desc", comment="情绪描述")
    limit_up = Column(Integer, name="limit_up", comment="涨停家数")
    limit_down = Column(Integer, name="limit_down", comment="跌停家数")
    limit_ratio = Column(Float, name="limit_ratio", comment="涨跌停比")
    sh_up_count = Column(Integer, name="sh_up_count", comment="沪市上涨")
    sh_down_count = Column(Integer, name="sh_down_count", comment="沪市下跌")
    sz_up_count = Column(Integer, name="sz_up_count", comment="深市上涨")
    sz_down_count = Column(Integer, name="sz_down_count", comment="深市下跌")
    created_at = Column(DateTime, default=func.now(), name="created_at", comment="记录创建时间")


class StockChangeHistory(Base):
    """股票异动历史"""

    __tablename__ = "stock_change_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    change_time = Column(String(10), name="change_time")
    change_date = Column(String(10), index=True, name="change_date")
    stock_code = Column(String(20), index=True, name="stock_code")
    stock_name = Column(String(50), name="stock_name")
    market = Column(Integer)
    change_type = Column(Integer, index=True, name="change_type")
    type_name = Column(String(20), name="type_name")
    volume = Column(BigInteger)
    price = Column(Float)
    change_rate = Column(Float, name="change_rate")
    amount = Column(Float)
    industry = Column(String(100))
    concept = Column(String(500))
    created_at = Column(DateTime, default=func.now(), name="created_at")

    __table_args__ = (
        Index(
            "idx_unique_change",
            "change_time",
            "change_date",
            "stock_code",
            "change_type",
            "volume",
            "price",
            "change_rate",
            "amount",
            unique=True,
        ),
    )


class WordAnalyze(GormBaseModel):
    """词频分析"""

    __tablename__ = "word_analyzes"

    data_time = Column(DateTime, index=True, default=func.now(), name="data_time")
    word = Column(String(100))
    frequency = Column(Integer)
    weight = Column(Float)
    score = Column(Float)


class SentimentResultAnalyze(GormBaseModel):
    """情感分析结果"""

    __tablename__ = "sentiment_result_analyzes"

    data_time = Column(DateTime, index=True, default=func.now(), name="data_time")
    score = Column(Float)
    category = Column(Integer)
    positive_count = Column(Integer, name="positive_count")
    negative_count = Column(Integer, name="negative_count")
    description = Column(Text)


class GlobalStockIndex(GormBaseModel):
    """全球股票指数"""

    __tablename__ = "global_stock_index"

    code = Column(String(20), index=True)
    name = Column(String(50))
    location = Column(String(50))
    qtcode = Column(String(50), index=True)
    state = Column(String(20))
    zdf = Column(String(20))
    zxj = Column(String(20))
    img = Column(String(500))
    region = Column(String(50), index=True)
    region_name = Column(String(50), name="region_name")


class LongTigerRankData(GormBaseModel):
    """龙虎榜数据"""

    __tablename__ = "long_tiger_rank"

    accum_amount = Column(Float, name="accum_amount")
    billboard_buy_amt = Column(Float, name="billboard_buy_amt")
    billboard_deal_amt = Column(Float, name="billboard_deal_amt")
    billboard_net_amt = Column(Float, name="billboard_net_amt")
    billboard_sell_amt = Column(Float, name="billboard_sell_amt")
    change_rate = Column(Float, name="change_rate")
    close_price = Column(Float, name="close_price")
    deal_amount_ratio = Column(Float, name="deal_amount_ratio")
    deal_net_ratio = Column(Float, name="deal_net_ratio")
    explain = Column(Text)
    explanation = Column(Text)
    free_market_cap = Column(Float, name="free_market_cap")
    secucode = Column(String(50), index=True)
    security_code = Column(String(20), name="security_code")
    security_name_abbr = Column(String(50), name="security_name_abbr")
    security_type_code = Column(String(20), name="security_type_code")
    trade_date = Column(String(20), index=True, name="trade_date")
    turnoverrate = Column(Float)
