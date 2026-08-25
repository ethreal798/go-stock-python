from fastapi import Response

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.user.token_blacklist import store_refresh_token


async def _issue_tokens(
    response: Response,
    user_id: int,
) -> dict:
    """为用户签发 Access Token 和 Refresh Token，并设置 httpOnly Cookie。

    Token 仅通过 Cookie 传递，不在响应体中返回。

    Args:
        response: FastAPI Response 对象
        user_id: 用户 ID
    """
    # 生成 Token
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # 解析 Refresh Token 获取 jti
    payload = decode_token(refresh_token)
    jti = payload.get("jti") if payload else None

    # 存储 Refresh Token 到 Redis
    refresh_expire_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    if jti:
        await store_refresh_token(user_id, jti, refresh_expire_seconds)

    # 设置 Cookie
    await _set_auth_cookies(response, access_token, refresh_token)

    return {}


async def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """在响应中设置 httpOnly Cookie。

    Args:
        response: FastAPI Response 对象
        access_token: Access Token
        refresh_token: Refresh Token
    """
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


async def _clear_auth_cookies(response: Response) -> None:
    """清除认证 Cookie。"""
    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        path="/",
    )
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/",
    )
