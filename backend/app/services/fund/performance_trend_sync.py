"""基金累计收益率走势快照同步。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from time import perf_counter
from typing import Any, Sequence
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.fund import Fund, FollowedFund, FundPerformanceTrendLatest
from app.services.fund.constants import FundCacheKeys
from app.services.fund.formatter import format_performance_trend_snapshot
from app.services.fund.performance_trend_source import PERIOD_TO_SOURCE_TYPE, fetch_performance_trend_payload
from app.services.fund.utils import delete_cache, normalize_fund_code

logger = logging.getLogger(__name__)


class FundPerformanceTrendSyncService:
    """同步被关注或明确指定的开放式基金最新绘图快照。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync_followed(
        self,
        *,
        periods: Sequence[str] | None = None,
        concurrency: int | None = None,
        batch_size: int | None = None,
        retries: int | None = None,
        timeout: float | None = None,
    ) -> dict[str, int]:
        """同步所有被至少一个用户关注的开放式基金。"""
        statement = (
            select(Fund)
            .join(FollowedFund, FollowedFund.fund_code == Fund.code)
            .where(Fund.status == "active", Fund.category == "open")
            .distinct()
            .order_by(Fund.id)
        )
        funds = list((await self.db.execute(statement)).scalars().all())
        return await self._sync_funds(
            funds,
            periods=periods,
            concurrency=concurrency,
            batch_size=batch_size,
            retries=retries,
            timeout=timeout,
        )

    async def fetch_and_sync_codes(
        self,
        fund_codes: Sequence[str],
        *,
        periods: Sequence[str],
        concurrency: int | None = None,
        batch_size: int | None = None,
        retries: int | None = None,
        timeout: float | None = None,
    ) -> dict[str, int]:
        """命令行或管理员操作按代码同步开放式基金。"""
        codes = list(dict.fromkeys(normalize_fund_code(code) for code in fund_codes))
        if not codes:
            return {"funds": 0, "snapshots": 0, "failed": 0}
        statement = select(Fund).where(Fund.code.in_(codes), Fund.status == "active", Fund.category == "open")
        funds = list((await self.db.execute(statement)).scalars().all())
        return await self._sync_funds(
            funds,
            periods=periods,
            concurrency=concurrency,
            batch_size=batch_size,
            retries=retries,
            timeout=timeout,
        )

    async def fetch_and_sync_one(
        self,
        fund: Fund,
        period: str,
        *,
        retries: int | None = None,
        timeout: float | None = None,
    ) -> FundPerformanceTrendLatest:
        """按需抓取并原子覆盖一只基金的一个周期。"""
        self._validate_periods((period,))
        retry_count = settings.FUND_TREND_FETCH_RETRIES if retries is None else retries
        request_timeout = settings.FUND_TREND_FETCH_TIMEOUT_SECONDS if timeout is None else timeout
        if retry_count < 0 or request_timeout <= 0:
            raise ValueError("retries 不能小于0，timeout 必须大于0")
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            snapshot = await self._fetch_snapshot(fund.code, period, client, retry_count)
        await self._upsert_snapshot(fund.id, snapshot)
        await self.db.commit()
        await self._invalidate_cache_safely(fund.code, period)
        return await self._get_snapshot(fund.id, period)

    async def _sync_funds(
        self,
        funds: Sequence[Fund],
        *,
        periods: Sequence[str] | None,
        concurrency: int | None,
        batch_size: int | None,
        retries: int | None,
        timeout: float | None,
    ) -> dict[str, int]:
        selected_periods = tuple(dict.fromkeys(periods or settings.FUND_TREND_SYNC_PERIODS))
        self._validate_periods(selected_periods)
        concurrency = settings.FUND_TREND_SYNC_CONCURRENCY if concurrency is None else concurrency
        batch_size = settings.FUND_TREND_SYNC_BATCH_SIZE if batch_size is None else batch_size
        retries = settings.FUND_TREND_FETCH_RETRIES if retries is None else retries
        timeout = settings.FUND_TREND_FETCH_TIMEOUT_SECONDS if timeout is None else timeout
        if concurrency < 1 or batch_size < 1 or retries < 0 or timeout <= 0:
            raise ValueError("concurrency、batch_size、timeout 必须大于0，retries 不能小于0")

        result = {"funds": len(funds), "snapshots": 0, "failed": 0}
        sync_id = uuid4().hex[:8]
        started_at = perf_counter()
        semaphore = asyncio.Semaphore(concurrency)
        logger.info(
            "event=fund_trend_sync.started sync_id=%s funds=%s periods=%s concurrency=%s",
            sync_id,
            len(funds),
            selected_periods,
            concurrency,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [(fund, period) for fund in funds for period in selected_periods]
            for offset in range(0, len(tasks), batch_size):
                batch = tasks[offset : offset + batch_size]
                responses = await asyncio.gather(
                    *[
                        self._fetch_with_semaphore(fund, period, client, retries, semaphore)
                        for fund, period in batch
                    ],
                    return_exceptions=True,
                )
                invalidated: list[tuple[str, str]] = []
                for (fund, period), response in zip(batch, responses):
                    if isinstance(response, BaseException):
                        result["failed"] += 1
                        logger.warning(
                            "event=fund_trend_sync.snapshot_failed sync_id=%s fund=%s period=%s error_type=%s error=%s",
                            sync_id,
                            fund.code,
                            period,
                            type(response).__name__,
                            response,
                        )
                        continue
                    await self._upsert_snapshot(fund.id, response)
                    invalidated.append((fund.code, period))
                    result["snapshots"] += 1
                await self.db.commit()
                for fund_code, period in invalidated:
                    await self._invalidate_cache_safely(fund_code, period)

        logger.info(
            "event=fund_trend_sync.completed sync_id=%s result=%s elapsed_seconds=%.2f",
            sync_id,
            result,
            perf_counter() - started_at,
        )
        return result

    async def _fetch_with_semaphore(
        self,
        fund: Fund,
        period: str,
        client: httpx.AsyncClient,
        retries: int,
        semaphore: asyncio.Semaphore,
    ) -> dict[str, Any]:
        async with semaphore:
            return await self._fetch_snapshot(fund.code, period, client, retries)

    async def _fetch_snapshot(
        self,
        fund_code: str,
        period: str,
        client: httpx.AsyncClient,
        retries: int,
    ) -> dict[str, Any]:
        for attempt in range(retries + 1):
            try:
                fetched_at = datetime.now()
                payload = await fetch_performance_trend_payload(fund_code, period, client=client)
                return format_performance_trend_snapshot(
                    payload,
                    fund_code=fund_code,
                    period=period,
                    fetched_at=fetched_at,
                    fresh_seconds=settings.FUND_TREND_FRESH_SECONDS,
                )
            except Exception:
                if attempt == retries:
                    raise
                await asyncio.sleep(min(2**attempt, 8))
        raise AssertionError("unreachable")

    async def _upsert_snapshot(self, fund_id: int, snapshot: dict[str, Any]) -> None:
        values = {**snapshot, "fund_id": fund_id}
        statement = pg_insert(FundPerformanceTrendLatest).values(values)
        update_columns = {
            key: getattr(statement.excluded, key)
            for key in values
            if key not in {"fund_id", "period", "created_at", "updated_at", "deleted_at"}
        }
        update_columns.update({"updated_at": func.now(), "deleted_at": None})
        await self.db.execute(
            statement.on_conflict_do_update(
                index_elements=[FundPerformanceTrendLatest.fund_id, FundPerformanceTrendLatest.period],
                set_=update_columns,
            )
        )

    async def _get_snapshot(self, fund_id: int, period: str) -> FundPerformanceTrendLatest:
        statement = select(FundPerformanceTrendLatest).where(
            FundPerformanceTrendLatest.fund_id == fund_id,
            FundPerformanceTrendLatest.period == period,
        )
        snapshot = (await self.db.execute(statement)).scalar_one()
        return snapshot

    @staticmethod
    def _validate_periods(periods: Sequence[str]) -> None:
        if not periods:
            raise ValueError("至少指定一个基金走势周期")
        unsupported = set(periods) - set(PERIOD_TO_SOURCE_TYPE)
        if unsupported:
            raise ValueError(f"不支持的基金走势周期: {sorted(unsupported)}")

    @staticmethod
    async def _invalidate_cache_safely(fund_code: str, period: str) -> None:
        try:
            await delete_cache(FundCacheKeys.performance_trend(fund_code, period))
        except Exception:
            logger.warning(
                "event=fund_trend.cache_invalidate_failed fund=%s period=%s",
                fund_code,
                period,
                exc_info=True,
            )
