"""基金累计收益率走势查询、缓存和按需刷新。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.redis import get_redis
from app.models.fund import Fund, FundPerformanceTrendLatest
from app.services.fund.common.constants import FundCacheKeys
from app.services.fund.common.utils import delete_cache, normalize_fund_code, read_json_cache, write_json_cache
from app.services.fund.sources.performance_trend import PERIOD_TO_SOURCE_TYPE
from app.services.fund.sync.performance_trend import FundPerformanceTrendSyncService

logger = logging.getLogger(__name__)


class FundPerformanceTrendNotFoundError(LookupError):
    """基金代码不存在。"""


class FundPerformanceTrendUnsupportedError(ValueError):
    """该基金分类不支持开放式基金累计收益率走势。"""


class FundPerformanceTrendUnavailableError(RuntimeError):
    """没有旧快照且上游暂时不可用。"""


class FundPerformanceTrendQueryService:
    """提供缓存优先、旧数据兜底的基金走势查询。"""

    LOCK_SECONDS = 60

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, fund_code: str, period: str) -> dict:
        if period not in PERIOD_TO_SOURCE_TYPE:
            raise ValueError(f"不支持的基金走势周期: {period}")
        code = normalize_fund_code(fund_code)

        cached = await self._read_cache_safely(code, period)
        if cached is not None:
            return cached

        fund = await self._get_fund(code)
        if fund is None:
            raise FundPerformanceTrendNotFoundError(code)
        # 调整 根据基金类型访问不同的净值
        if fund.category != "open":
            raise FundPerformanceTrendUnsupportedError(f"基金 {code} 不是开放式基金")

        snapshot = await self._get_snapshot(fund.id, period)
        if snapshot is not None and snapshot.expires_at > datetime.now():
            response = self._response(fund.code, snapshot, is_stale=False)
            await self._write_cache_safely(fund.code, period, response, stale=False)
            return response

        # rollback 会使 ORM 对象过期，因此刷新前先保存旧响应和基础标识。
        fund_code_value = fund.code
        stale_response = self._response(fund_code_value, snapshot, is_stale=True) if snapshot is not None else None
        lock_key = f"fund:performance-trend:lock:{fund_code_value}:{period}"
        lock_token = uuid4().hex
        redis = None
        try:
            redis = await get_redis()
            acquired = await redis.set(lock_key, lock_token, nx=True, ex=self.LOCK_SECONDS)
        except Exception:
            # Redis 是优化层；不可用时允许当前请求直接刷新，数据库仍是事实来源。
            acquired = True
            logger.warning(
                "event=fund_trend.lock_unavailable fund=%s period=%s",
                fund.code,
                period,
                exc_info=True,
            )
        if acquired:
            try:
                try:
                    snapshot = await FundPerformanceTrendSyncService(self.db).fetch_and_sync_one(fund, period)
                    response = self._response(fund_code_value, snapshot, is_stale=False)
                    await self._write_cache_safely(fund_code_value, period, response, stale=False)
                    return response
                except Exception as exc:
                    await self.db.rollback()
                    if stale_response is None:
                        raise FundPerformanceTrendUnavailableError(
                            f"基金 {fund_code_value} 的 {period} 走势暂时无法获取"
                        ) from exc
                    logger.warning(
                        "event=fund_trend.on_demand_refresh_failed fund=%s period=%s error_type=%s error=%s",
                        fund_code_value,
                        period,
                        type(exc).__name__,
                        exc,
                    )
                    await self._write_cache_safely(fund_code_value, period, stale_response, stale=True)
                    return stale_response
            finally:
                if redis is not None:
                    try:
                        await self._release_lock(redis, lock_key, lock_token)
                    except Exception:
                        logger.warning(
                            "event=fund_trend.lock_release_failed fund=%s period=%s",
                            fund_code_value,
                            period,
                            exc_info=True,
                        )

        # 另一个请求正在刷新：有旧快照立即返回，没有则短暂等待其写入缓存。
        if stale_response is not None:
            await self._write_cache_safely(fund_code_value, period, stale_response, stale=True)
            return stale_response
        for _ in range(10):
            await asyncio.sleep(0.2)
            cached = await self._read_cache_safely(fund_code_value, period)
            if cached is not None:
                return cached
        raise FundPerformanceTrendUnavailableError(f"基金 {fund_code_value} 的 {period} 走势正在生成")

    async def _get_fund(self, fund_code: str) -> Fund | None:
        return (await self.db.execute(select(Fund).where(Fund.code == fund_code))).scalar_one_or_none()

    async def _get_snapshot(self, fund_id: int, period: str) -> FundPerformanceTrendLatest | None:
        statement = select(FundPerformanceTrendLatest).where(
            FundPerformanceTrendLatest.fund_id == fund_id,
            FundPerformanceTrendLatest.period == period,
        )
        return (await self.db.execute(statement)).scalar_one_or_none()

    @staticmethod
    def _response(fund_code: str, snapshot: FundPerformanceTrendLatest, *, is_stale: bool) -> dict:
        return {
            "fund_code": fund_code,
            "period": snapshot.period,
            "start_date": snapshot.start_date.isoformat(),
            "end_date": snapshot.end_date.isoformat(),
            "fetched_at": snapshot.fetched_at.isoformat(),
            "is_stale": is_stale,
            "series": snapshot.series_data,
        }

    @staticmethod
    async def _release_lock(redis, lock_key: str, lock_token: str) -> None:
        await redis.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            lock_key,
            lock_token,
        )

    @staticmethod
    async def _read_cache_safely(fund_code: str, period: str) -> dict | None:
        try:
            cache_key = FundCacheKeys.performance_trend(fund_code, period)
            payload = await read_json_cache(cache_key)
            if payload is not None and not isinstance(payload, dict):
                await delete_cache(cache_key)
                return None
            return payload
        except Exception:
            logger.warning(
                "event=fund_trend.cache_read_failed fund=%s period=%s",
                fund_code,
                period,
                exc_info=True,
            )
            return None

    @staticmethod
    async def _write_cache_safely(fund_code: str, period: str, payload: dict, *, stale: bool) -> None:
        try:
            await write_json_cache(
                FundCacheKeys.performance_trend(fund_code, period),
                payload,
                ttl_seconds=300 if stale else settings.FUND_TREND_CACHE_TTL_SECONDS,
                jitter_seconds=0 if stale else 3600,
            )
        except Exception:
            logger.warning(
                "event=fund_trend.cache_write_failed fund=%s period=%s",
                fund_code,
                period,
                exc_info=True,
            )
