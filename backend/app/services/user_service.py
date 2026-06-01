"""用户业务逻辑服务。"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, TokenPayload

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类，处理注册、登录及权限校验。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户。"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """验证用户登录。"""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        await self.db.commit()
        return user

    async def register(self, user_in: UserCreate) -> User:
        """注册新用户。"""
        # 检查邮箱是否已存在
        existing_user = await self.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )
        
        # 创建新用户
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_superuser=user_in.is_superuser,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def get_current_user(self, token: str) -> User:
        """从 Token 中解析并获取当前用户。"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_data = TokenPayload(sub=int(user_id))
        except (JWTError, ValueError):
            raise credentials_exception
        
        result = await self.db.execute(select(User).where(User.id == token_data.sub))
        user = result.scalars().first()
        
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
            
        return user
