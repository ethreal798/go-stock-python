"""基金累计收益率走势快照同步。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Sequence

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.fund import Fund, FundPerformanceTrendLatest, FundWatchlistItem
from app.services.fund.common.constants import FundCacheKeys
from app.services.fund.common.formatter import format_performance_trend_snapshot
from app.services.fund.common.utils import delete_cache, normalize_fund_code
from app.services.fund.sources.performance_trend import PERIOD_TO_SOURCE_TYPE, fetch_performance_trend_payload

logger = logging.getLogger(__name__)


class FundPerformanceTrendSyncService:
    """同步自选列表中或明确指定的开放式基金最新绘图快照。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # async def fetch_and_sync_watchlist(
    #     self,
    #     *,
    #     periods: Sequence[str] | None = None,
    #     concurrency: int | None = None,
    #     batch_size: int | None = None,
    #     retries: int | None = None,
    #     timeout: float | None = None,
    # ) -> dict[str, int]:
    #     """同步至少被一个用户加入自选的开放式基金。"""
    #     statement = (
    #         select(Fund)
    #         .join(FundWatchlistItem, FundWatchlistItem.fund_code == Fund.code)
    #         .where(Fund.status == "active", Fund.category == "open")
    #         .distinct()
    #         .order_by(Fund.id)
    #     )
    #     funds = list((await self.db.execute(statement)).scalars().all())
    #     return await self._sync_funds(
    #         funds,
    #         periods=periods,
    #         concurrency=concurrency,
    #         batch_size=batch_size,
    #         retries=retries,
    #         timeout=timeout,
    #     )

    async def fetch_and_sync_codes(
        self,
        fund_codes: Sequence[str],
        *,
        periods: Sequence[str],
        concurrency: int = 4,
        batch_size: int = 20,
        retries: int = 2,
        timeout: float = 10.0,
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
        retries: int = 2,
        timeout: float = 10.0,
    ) -> FundPerformanceTrendLatest:
        """按需抓取并原子覆盖一只基金的一个周期。"""
        if retries < 0 or timeout <= 0:
            raise ValueError("retries 不能小于0，timeout 必须大于0")
        async with httpx.AsyncClient(timeout=timeout) as client:
            snapshot = await self._fetch_snapshot(fund.code, period, client, retries)
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
        selected_periods = tuple(dict.fromkeys(periods))

        result = {"funds": len(funds), "snapshots": 0, "failed": 0}
        semaphore = asyncio.Semaphore(concurrency)
        logger.info(f"开始同步基金走势：共 {len(funds)} 只基金，周期 {selected_periods}，并发 {concurrency}")
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [(fund, period) for fund in funds for period in selected_periods]
            for offset in range(0, len(tasks), batch_size):
                batch = tasks[offset: offset + batch_size]
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
                        logger.warning(f"基金 {fund.code} 周期 {period} 同步失败：{response}")
                        continue
                    await self._upsert_snapshot(fund.id, response)
                    invalidated.append((fund.code, period))
                    result["snapshots"] += 1
                await self.db.commit()
                for fund_code, period in invalidated:
                    await self._invalidate_cache_safely(fund_code, period)

        logger.info(f"基金走势同步完成：{result}")
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
        """获取基金的最新快照数据"""
        statement = select(FundPerformanceTrendLatest).where(
            FundPerformanceTrendLatest.fund_id == fund_id,
            FundPerformanceTrendLatest.period == period,
        )
        snapshot = (await self.db.execute(statement)).scalar_one()
        return snapshot

    @staticmethod
    async def _invalidate_cache_safely(fund_code: str, period: str) -> None:
        try:
            await delete_cache(FundCacheKeys.performance_trend(fund_code, period))
        except Exception:
            logger.warning(f"基金 {fund_code} 周期 {period} 缓存清理失败", exc_info=True)
