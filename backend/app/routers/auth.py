"""认证相关路由。"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import Token, UserCreate, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 密码模式配置，Token 路由地址
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("/register", response_model=UserOut, summary="用户注册")
async def register(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
) -> Any:
    """注册新账号。"""
    return await service.register(user_in)


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
) -> Any:
    """OAuth2 兼容登录，返回访问令牌。
    
    注意：在 Swagger/OpenAPI 中，'username' 字段应填写注册时的 'email'。
    """
    user = await service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
async def get_me(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service)
) -> Any:
    """获取当前登录用户的详细资料。"""
    return await service.get_current_user(token)
