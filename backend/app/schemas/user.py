"""用户相关的 Pydantic 模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---- 属性基类 ----
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None


# ---- 创建用户时的输入（不含权限字段，防止 mass assignment） ----
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None


# ---- API 返回的用户信息 (排除敏感字段) ----
class UserOut(UserBase):
    id: int
    username: str
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
