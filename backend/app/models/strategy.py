"""策略模型"""

from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text
from .base import Base, TimestampMixin


class CustomStrategy(Base, TimestampMixin):
    """自定义策略"""
    __tablename__ = "custom_strategies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    description = Column(String(500))
    sort_order = Column(Integer, default=0, server_default="0", name="sort_order")
