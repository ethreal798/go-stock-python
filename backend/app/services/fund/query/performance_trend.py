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

    async def get_trend(self, fund_code: str, period: str) -> dict:
        if period not in PERIOD_TO_SOURCE_TYPE:
            raise ValueError(f"不支持的基金走势周期: {period}")
        code = normalize_fund_code(fund_code)

        # 1. redis中如果有记录 则直接返回
        cached = await self._read_cache_safely(code, period)
        if cached is not None:
            return cached

        # 2. 校验传入的基金代码是否有效
        fund = await self._get_fund(code)
        if fund is None:
            raise FundPerformanceTrendNotFoundError(code)
        if fund.is_exchange:
            raise FundPerformanceTrendUnsupportedError(f"基金 {code} 是场内基金，请查看K线")

        # 3. 根据基金类型调用对应的同步方法
        sync_service = FundPerformanceTrendSyncService(self.db)
        refresh_fn = sync_service.fetch_and_sync_money if fund.is_hb else sync_service.fetch_and_sync_one
        unavailable_msg = (
            f"货币基金 {code} 的 {period} 走势暂时无法获取"
            if fund.is_hb
            else f"基金 {code} 的 {period} 走势暂时无法获取"
        )

        # 4. 获取最新快照 当快照存在且数据未过期 直接返回
        snapshot = await self._get_snapshot(fund.id, period)
        if snapshot is not None and snapshot.expires_at > datetime.now():
            response = self._response(fund.code, fund.is_hb, snapshot, is_stale=False)
            # 将快照数据写入redis
            await self._write_cache_safely(fund.code, period, response, stale=False)
            return response

        fund_code_value = fund.code
        # 6. 保存旧快照数据，准备进行原子刷新
        stale_response = (
            self._response(fund_code_value, fund.is_hb, snapshot, is_stale=True) if snapshot is not None else None
        )
        lock_key = f"fund:performance-trend:lock:{fund_code_value}:{period}"
        lock_token = uuid4().hex
        redis = None
        try:
            # 获取redis客户端
            redis = await get_redis()
            # 获取原子锁
            acquired = await redis.set(lock_key, lock_token, nx=True, ex=self.LOCK_SECONDS)
        except Exception:
            acquired = True
            logger.warning("获取锁失败，直接执行刷新：基金 %s，周期 %s", fund.code, period)
        # 7. 只要拿到原子锁的哪个线程才能执行刷新操作
        if acquired:
            try:
                try:
                    # 执行刷新获取指定周期的最新快照
                    snapshot = await refresh_fn(fund, period)
                    response = self._response(fund_code_value, fund.is_hb, snapshot, is_stale=False)
                    await self._write_cache_safely(fund_code_value, period, response, stale=False)
                    return response
                except Exception as exc:
                    # 刷新过程中 出现异常 存在旧数据则使用旧数据兜底返回，否则抛出异常
                    await self.db.rollback()
                    if stale_response is None:
                        raise FundPerformanceTrendUnavailableError(unavailable_msg) from exc
                    logger.warning(
                        "刷新失败，返回旧快照：基金 %s，周期 %s，错误 %s",
                        fund_code_value,
                        period,
                        exc,
                    )
                    await self._write_cache_safely(fund_code_value, period, stale_response, stale=True)
                    return stale_response
            finally:
                # 不论什么情况最终都需要释放redis连接
                if redis is not None:
                    try:
                        await self._release_lock(redis, lock_key, lock_token)
                    except Exception:
                        logger.warning("释放锁失败：基金 %s，周期 %s", fund_code_value, period)

        # 8. 其他线程获取不到锁时则会进入这里，如果存在旧数据则先返回
        if stale_response is not None:
            await self._write_cache_safely(fund_code_value, period, stale_response, stale=True)
            return stale_response
        # 没有旧快照数据 进行2s等待 每0.2s向redis中读缓存
        for _ in range(10):
            await asyncio.sleep(0.2)
            cached = await self._read_cache_safely(fund_code_value, period)
            if cached is not None:
                return cached
        raise FundPerformanceTrendUnavailableError(f"基金 {fund_code_value} 的 {period} 走势正在生成")

    async def _get_fund(self, fund_code: str) -> Fund | None:
        """从基金主表获取基金信息"""
        return (await self.db.execute(select(Fund).where(Fund.code == fund_code))).scalar_one_or_none()

    async def _get_snapshot(self, fund_id: int, period: str) -> FundPerformanceTrendLatest | None:
        """从历史收益率表读取基金对应周期的快照数据"""
        statement = select(FundPerformanceTrendLatest).where(
            FundPerformanceTrendLatest.fund_id == fund_id,
            FundPerformanceTrendLatest.period == period,
        )
        return (await self.db.execute(statement)).scalar_one_or_none()

    @staticmethod
    def _response(fund_code: str, is_hb: bool, snapshot: FundPerformanceTrendLatest, *, is_stale: bool) -> dict:
        """组装schema中要求的数据结构"""
        return {
            "fund_code": fund_code,
            "is_hb": is_hb,
            "period": snapshot.period,
            "start_date": snapshot.start_date.isoformat(),
            "end_date": snapshot.end_date.isoformat(),
            "fetched_at": snapshot.fetched_at.isoformat(),
            "is_stale": is_stale,
            "series": snapshot.series_data,
        }

    @staticmethod
    async def _release_lock(redis, lock_key: str, lock_token: str) -> None:
        """释放原子锁"""
        await redis.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then " "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            lock_key,
            lock_token,
        )

    @staticmethod
    async def _read_cache_safely(fund_code: str, period: str) -> dict | None:
        """读取redis对应基金的缓存数据"""
        try:
            cache_key = FundCacheKeys.performance_trend(fund_code, period)
            payload = await read_json_cache(cache_key)
            if payload is not None and not isinstance(payload, dict):
                await delete_cache(cache_key)
                return None
            return payload
        except Exception:
            logger.warning("读取缓存失败：基金 %s，周期 %s", fund_code, period)
            return None

    @staticmethod
    async def _write_cache_safely(fund_code: str, period: str, payload: dict, *, stale: bool) -> None:
        """向redis中写入缓存数据"""
        try:
            await write_json_cache(
                FundCacheKeys.performance_trend(fund_code, period),
                payload,
                ttl_seconds=300 if stale else settings.FUND_TREND_CACHE_TTL_SECONDS,
                jitter_seconds=0 if stale else 3600,
            )
        except Exception:
            logger.warning("写入缓存失败：基金 %s，周期 %s", fund_code, period)
