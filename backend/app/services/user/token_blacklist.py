"""Token 黑名单服务 — 基于 Redis。

用于登出时失效 Token，防止已泄露的 Token 继续被使用。
"""

import logging
from typing import Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Redis key 前缀
_BLACKLIST_PREFIX = "token:blacklist:"
_REFRESH_TOKEN_PREFIX = "refresh_token:"


async def blacklist_access_token(token: str, expire_seconds: int) -> None:
    """将 Access Token 加入黑名单。

    Args:
        token: JWT Token 字符串
        expire_seconds: 过期秒数（通常等于 Token 剩余有效期）
    """
    if expire_seconds <= 0:
        return
    redis = await get_redis()
    key = f"{_BLACKLIST_PREFIX}{token}"
    await redis.setex(key, expire_seconds, "1")
    logger.info("Access token blacklisted, ttl=%ds", expire_seconds)


async def is_token_blacklisted(token: str) -> bool:
    """检查 Token 是否在黑名单中。"""
    redis = await get_redis()
    key = f"{_BLACKLIST_PREFIX}{token}"
    return bool(await redis.exists(key))


async def store_refresh_token(user_id: int, jti: str, expire_seconds: int) -> None:
    """存储 Refresh Token 的 jti 到 Redis（用于验证和登出）。

    Args:
        user_id: 用户 ID
        jti: Refresh Token 的唯一 ID
        expire_seconds: 过期秒数
    """
    if expire_seconds <= 0:
        return
    redis = await get_redis()
    key = f"{_REFRESH_TOKEN_PREFIX}{user_id}"
    # 使用 SET 存储 jti，支持同一用户只有一个有效 refresh token
    # 如需支持多设备，可改用 SETNX 存储多个 jti，每个设备一个
    await redis.setex(key, expire_seconds, jti)
    logger.info("Refresh token stored for user %d, jti=%s, ttl=%ds", user_id, jti, expire_seconds)


async def validate_refresh_token(user_id: int, jti: str) -> bool:
    """验证 Refresh Token 的 jti 是否与 Redis 中存储的匹配。

    Args:
        user_id: 用户 ID
        jti: Refresh Token 的唯一 ID

    Returns:
        True 表示有效，False 表示已失效或不匹配
    """
    redis = await get_redis()
    key = f"{_REFRESH_TOKEN_PREFIX}{user_id}"
    stored_jti = await redis.get(key)
    if stored_jti and stored_jti == jti:
        return True
    return False


async def revoke_refresh_token(user_id: int) -> None:
    """删除用户的 Refresh Token（登出时调用）。"""
    redis = await get_redis()
    key = f"{_REFRESH_TOKEN_PREFIX}{user_id}"
    await redis.delete(key)
    logger.info("Refresh token revoked for user %d", user_id)


async def get_stored_refresh_jti(user_id: int) -> Optional[str]:
    """获取用户当前存储的 Refresh Token jti。"""
    redis = await get_redis()
    key = f"{_REFRESH_TOKEN_PREFIX}{user_id}"
    return await redis.get(key)
