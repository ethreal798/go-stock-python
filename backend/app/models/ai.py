"""AI 相关模型"""

from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Boolean, Float, Text, func
from .base import Base, GormBaseModel, TimestampMixin


class AIResponseResult(GormBaseModel):
    """AI 响应结果"""

    __tablename__ = "ai_response_result"

    chat_id = Column(String(100), name="chat_id")
    model_name = Column(String(100), name="model_name")
    stock_code = Column(String(20), name="stock_code")
    stock_name = Column(String(50), name="stock_name")
    question = Column(Text)
    content = Column(Text)
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")


class AIRecommendStocks(GormBaseModel):
    """AI 推荐股票"""

    __tablename__ = "ai_recommend_stocks"

    data_time = Column(DateTime, index=True, name="data_time")
    model_name = Column(String(100), name="model_name")
    rating = Column(String(20))
    stock_code = Column(String(20), name="stock_code")
    stock_name = Column(String(50), name="stock_name")
    bk_code = Column(String(50), name="bk_code")
    bk_name = Column(String(100), name="bk_name")
    stock_price = Column(String(20), name="stock_price")
    stock_current_price = Column(String(20), name="stock_current_price")
    stock_current_price_time = Column(String(50), name="stock_current_price_time")
    stock_close_price = Column(String(20), name="stock_close_price")
    stock_pre_price = Column(String(20), name="stock_pre_price")
    recommend_reason = Column(Text, name="recommend_reason")
    recommend_buy_price = Column(String(50), name="recommend_buy_price")
    recommend_buy_price_min = Column(Float, name="recommend_buy_price_min")
    recommend_buy_price_max = Column(Float, name="recommend_buy_price_max")
    recommend_stop_profit_price = Column(String(50), name="recommend_stop_profit_price")
    recommend_stop_profit_price_min = Column(Float, name="recommend_stop_profit_price_min")
    recommend_stop_profit_price_max = Column(Float, name="recommend_stop_profit_price_max")
    recommend_stop_loss_price = Column(String(50), name="recommend_stop_loss_price")
    risk_remarks = Column(Text, name="risk_remarks")
    remarks = Column(Text)
    enable_alert = Column(Boolean, default=False, server_default="0", name="enable_alert")


class PromptTemplate(Base, TimestampMixin):
    """提示词模板"""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    content = Column(Text)
    type = Column(String(50))


class ChatMemory(Base):
    """聊天记忆"""

    __tablename__ = "chat_memory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, name="session_id")
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now(), name="created_at")
