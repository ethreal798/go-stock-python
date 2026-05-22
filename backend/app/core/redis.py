"""Redis 异步连接管理。"""

from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

# 全局 Redis 连接池
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 异步客户端实例。

    使用方式::
        redis = await get_redis()
        await redis.set("key", "value")
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    """关闭 Redis 连接池。"""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
