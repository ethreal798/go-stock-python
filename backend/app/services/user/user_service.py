"""用户业务逻辑服务。"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

# 不存在用户时使用的 dummy 哈希（新格式），用于防止时序攻击
_DUMMY_HASH = "sha256$2b$12$C9ixdp2MHMZvRqPWOfWzZOb6XkQiKqHg7KbQrOxP1nJqYHnJMxRWK"


class UserService:
    """用户服务类，处理注册、登录及权限校验。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户。"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户。"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """验证用户登录。

        安全说明：对不存在的用户也执行一次 dummy bcrypt 校验，
        防止通过响应时间差枚举用户（时序攻击）。
        """
        user = await self.get_by_email(email)
        if not user:
            # 对不存在的用户也执行 dummy 校验，使用固定哈希值
            # 使响应时间与存在用户时相近，防止时序攻击
            verify_password(password, _DUMMY_HASH)
            return None
        if not verify_password(password, user.hashed_password):
            return None

        # 更新最后登录时间
        user.last_login = datetime.now()
        await self.db.commit()
        return user

    async def register(self, user_in: UserCreate) -> User:
        """注册新用户。

        安全说明：is_superuser 强制为 False，防止 mass assignment 提权；
        捕获 IntegrityError 防止并发注册时返回 500 错误。
        """
        # 检查邮箱是否已存在
        if await self.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        if await self.get_by_username(user_in.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

        # 创建新用户 — is_superuser 硬编码为 False，不接受用户输入
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_superuser=False,
        )
        self.db.add(db_user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱或用户名已被注册",
            )
        await self.db.refresh(db_user)
        return db_user

    async def get_current_user(self, token: str) -> User:
        """从 Token 中解析并获取当前用户。

        安全说明：只接受 type=access 的 Token，防止 Refresh Token 被误用。
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

        from app.core.security import decode_token

        payload = decode_token(token)
        if not payload:
            raise credentials_exception

        # 验证 Token 类型必须是 access
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()

        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")

        return user
