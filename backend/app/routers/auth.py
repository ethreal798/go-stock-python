"""认证相关路由 — 支持 Access Token + Refresh Token + httpOnly Cookie。

安全特性：
- Access Token：短期有效（默认 1 小时），存储于 httpOnly Cookie
- Refresh Token：长期有效（默认 7 天），存储于 httpOnly Cookie
- 登出时 Refresh Token 在服务端（Redis）失效
- 所有敏感接口受速率限制保护
- 认证支持 Cookie 和 Authorization Header 两种方式（向后兼容）
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.rate_limiter import get_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.user.token_blacklist import (
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)
from app.services.user.user_service import UserService
from app.services.user.utils import _clear_auth_cookies, _issue_tokens, _set_auth_cookies

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# 获取限流器实例
limiter = get_limiter()

# OAuth2 密码模式配置 — 保留用于 Authorization Header 向后兼容
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login",
    auto_error=False,  # 不自动报错，手动处理
)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def _extract_access_token(
    access_token_cookie: Optional[str] = Cookie(None, alias=settings.ACCESS_TOKEN_COOKIE_NAME),
) -> Optional[str]:
    """从 Cookie 或  Header 中提取 Access Token。"""
    if access_token_cookie:
        return access_token_cookie
    return None


async def get_current_user(
    response: Response,
    token: Optional[str] = Depends(_extract_access_token),
    refresh_token_cookie: Optional[str] = Cookie(None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
    service: UserService = Depends(get_user_service),
) -> User:
    """获取当前用户
    若 Access Token 过期且存在有效 Refresh Token，自动续期。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 尝试 Access Token
    if token:
        user = await service.get_current_user(token)
        if user:
            return user

    # Access Token 无效，尝试 Refresh Token 自动续期
    if refresh_token_cookie:
        payload = decode_token(refresh_token_cookie)
        if payload and payload.get("type") == "refresh":
            user_id = payload.get("sub")
            jti = payload.get("jti")
            if user_id and jti:
                if await validate_refresh_token(int(user_id), jti):
                    # 检查用户状态
                    result = await service.db.execute(select(User).where(User.id == int(user_id)))
                    user = result.scalars().first()
                    if user and user.is_active:
                        # 自动续期：签发新的 Token 对
                        new_access_token = create_access_token(user_id)
                        new_refresh_token = create_refresh_token(user_id)
                        new_payload = decode_token(new_refresh_token)
                        new_jti = new_payload.get("jti") if new_payload else None
                        if new_jti:
                            refresh_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
                            await store_refresh_token(int(user_id), new_jti, refresh_expire)
                        # 设置新 Cookie
                        await _set_auth_cookies(response, new_access_token, new_refresh_token)
                        # 返回用户
                        return await service.get_current_user(new_access_token)

    raise credentials_exception


async def get_current_user_optional(
    response: Response,
    token: Optional[str] = Depends(_extract_access_token),
    refresh_token_cookie: Optional[str] = Cookie(None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
    service: UserService = Depends(get_user_service),
) -> Optional[User]:
    """获取当前用户（可选）— 未登录返回 None，不抛出异常。"""
    try:
        return await get_current_user(
            response=response,
            token=token,
            refresh_token_cookie=refresh_token_cookie,
            service=service,
        )
    except HTTPException:
        return None


# ============================================================
# 路由定义
# ============================================================


@router.post("/register", summary="用户注册")
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
) -> dict:
    """注册新账号。

    速率限制：每个 IP 每分钟最多 3 次注册请求。
    注册成功后自动登录，Token 通过 httpOnly Cookie 返回。
    """
    new_user = await service.register(user_in)
    return await _issue_tokens(response, new_user.id)


@router.post("/login", summary="用户登录")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> dict:
    """OAuth2 兼容登录，Token 通过 httpOnly Cookie 返回。

    速率限制：每个 IP 每分钟最多 5 次登录尝试，防止暴力破解。

    注意：在 Swagger/OpenAPI 中，'username' 字段应填写注册时的 'email'。
    """
    user = await service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _issue_tokens(response, user.id)


@router.post("/refresh", summary="刷新 Access Token")
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
    service: UserService = Depends(get_user_service),
) -> dict:
    """使用 Refresh Token 获取新的 Access Token。

    Refresh Token 轮换策略：每次刷新后旧 Refresh Token 失效，签发新的。
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Refresh Token",
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Refresh Token",
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 格式错误",
        )

    # 验证 Refresh Token 是否在 Redis 中有效
    if not await validate_refresh_token(int(user_id), jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 已失效，请重新登录",
        )

    # 检查用户状态
    result = await service.db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    # 签发新的 Token 对（Refresh Token 轮换）
    return await _issue_tokens(response, int(user_id))


@router.post("/logout", summary="用户登出")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
) -> dict:
    """用户登出。

    失效 Refresh Token（Redis 黑名单），清除所有 Cookie。
    """
    # 解析 Refresh Token 获取用户 ID 并失效
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                await revoke_refresh_token(int(user_id))

    # 清除 Cookie
    await _clear_auth_cookies(response)

    return {}


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取当前登录用户的详细资料。

    支持 httpOnly Cookie 和 Authorization Header 两种认证方式，
    Access Token 过期时自动用 Refresh Token 续期。
    """
    return current_user
