"""基础模型类和 Mixin"""

from sqlalchemy import Column, BigInteger, DateTime, func, Integer

# 复用项目已有的声明基类，保证 Alembic env.py 中的 target_metadata 一致
from app.core.database import Base


class TimestampMixin:
    """时间戳 Mixin：自动记录创建和更新时间"""
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SoftDeleteMixin:
    """软删除 Mixin：deleted_at 为 None 表示未删除"""
    deleted_at = Column(DateTime, nullable=True, index=True)


class GormBaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """对应 Go 中 gorm.Model 的基础模型"""
    __abstract__ = True
    id = Column(BigInteger, primary_key=True, autoincrement=True)
