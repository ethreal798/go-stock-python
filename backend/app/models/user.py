"""用户模型。"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from .base import GormBaseModel


class User(GormBaseModel):
    """系统用户"""

    __tablename__ = "users"

    username = Column(String(100), unique=True, index=True, nullable=False, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="哈希密码")
    email = Column(String(100), unique=True, index=True, nullable=True, comment="电子邮箱")
    full_name = Column(String(100), nullable=True, comment="姓名")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否为超级管理员")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
