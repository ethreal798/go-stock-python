"""开放式/场内基金净值与货币基金收益历史同步。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from math import ceil
from time import perf_counter
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundMoneyYieldHistory, FundOpenExchangeNavHistory
from app.services.fund.common.utils import iter_batches, normalize_date, normalize_decimal, normalize_fund_code
from app.services.fund.sources.history import fetch_money_yield_frame, fetch_open_or_exchange_nav_frames

logger = logging.getLogger(__name__)

HISTORY_UPSERT_BATCH_SIZE = 500
HistoryModel = type[FundOpenExchangeNavHistory] | type[FundMoneyYieldHistory]


class FundHistorySyncService:
    """按基金分类抓取历史数据并幂等写入。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync_all(
        self,
        *,
        concurrency: int = 4,
        batch_size: int = 20,
        retries: int = 2,
    ) -> dict[str, int]:
        """游标分页同步全部基金历史"""
        if concurrency < 1 or batch_size < 1 or retries < 0:
            raise ValueError("concurrency、batch_size 必须大于 0，retries 不能小于 0")

        total = int((await self.db.execute(select(func.count(Fund.id)))).scalar_one())
        result = {"funds": 0, "rows": 0, "failed": 0}
        if total == 0:
            logger.info("没有需要同步的基金")
            return result

        total_batches = ceil(total / batch_size)
        semaphore = asyncio.Semaphore(concurrency)
        last_id = 0
        batch_index = 0
        logger.info(f"开始全量同步：共 {total} 只基金，分 {total_batches} 批，并发 {concurrency}，重试 {retries}")

        while result["funds"] < total:
            batch_index += 1
            statement = (
                select(Fund)
                .where(Fund.id > last_id)
                .order_by(Fund.id)
                .limit(min(batch_size, total - result["funds"]))
            )
            fund_batch = list((await self.db.execute(statement)).scalars().all())
            if not fund_batch:
                logger.warning(f"游标提前结束：已处理 {result['funds']} / {total} 只，last_id={last_id}")
                break
            last_id = fund_batch[-1].id

            responses = await asyncio.gather(
                *(self._sync_one(fund, retries=retries, semaphore=semaphore) for fund in fund_batch),
                return_exceptions=True,
            )
            values_by_model: dict[HistoryModel, list[dict[str, Any]]] = {}
            for fund, response in zip(fund_batch, responses):
                result["funds"] += 1
                if isinstance(response, Exception):
                    result["failed"] += 1
                    logger.warning(f"基金 {fund.code} {fund.name} 同步失败：{response}")
                    continue
                model, values = response
                values_by_model.setdefault(model, []).extend(values)

            for model, values in values_by_model.items():
                if values:
                    await self._upsert_history(model, values)
                    result["rows"] += len(values)
            await self.db.commit()

        logger.info(f"全量同步完成：处理 {result['funds']} 只，写入 {result['rows']} 行，失败 {result['failed']} 只")
        return result

    async def sync_by_fund_codes(
        self,
        fund_codes: Sequence[str],
        *,
        retries: int = 2,
    ) -> dict[str, int]:
        """按指定基金代码逐只同步，不使用并发或分页。"""
        if retries < 0:
            raise ValueError("retries 不能小于 0")
        normalized_codes = list(dict.fromkeys(normalize_fund_code(code) for code in fund_codes))
        if not normalized_codes:
            return {"funds": 0, "rows": 0, "failed": 0}

        statement = select(Fund).where(Fund.code.in_(normalized_codes))
        funds = list((await self.db.execute(statement)).scalars().all())
        funds_by_code = {fund.code: fund for fund in funds}

        result = {"funds": 0, "rows": 0, "failed": 0}
        values_by_model: dict[HistoryModel, list[dict[str, Any]]] = {}
        for code in normalized_codes:
            fund = funds_by_code.get(code)
            result["funds"] += 1
            if fund is None:
                result["failed"] += 1
                logger.warning(f"基金 {code} 不存在，跳过同步")
                continue
            try:
                model, values = await self._sync_one(fund, retries=retries)
            except Exception as exc:
                result["failed"] += 1
                fund_type = "货币基金" if fund.is_hb else "其他基金"
                logger.warning(f"基金 {fund.code}（{fund_type}）同步失败：{exc}")
                continue
            values_by_model.setdefault(model, []).extend(values)

        for model, values in values_by_model.items():
            if values:
                await self._upsert_history(model, values)
                result["rows"] += len(values)
        await self.db.commit()
        return result

    async def _sync_one(
        self,
        fund: Fund,
        *,
        retries: int,
        semaphore: asyncio.Semaphore | None = None,
    ) -> tuple[HistoryModel, list[dict[str, Any]]]:
        """按基金分类抓取数据并归一化为可入库记录。"""
        if semaphore is None:
            return await self._fetch_and_normalize(fund, retries=retries)
        async with semaphore:
            return await self._fetch_and_normalize(fund, retries=retries)

    async def _fetch_and_normalize(
        self,
        fund: Fund,
        *,
        retries: int,
    ) -> tuple[HistoryModel, list[dict[str, Any]]]:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                fetched_at = datetime.now()
                if fund.is_hb:
                    raw_rows = await asyncio.to_thread(fetch_money_yield_frame, fund.code)
                    model: HistoryModel = FundMoneyYieldHistory
                else:
                    raw_rows = await asyncio.to_thread(fetch_open_or_exchange_nav_frames, fund.code)
                    model = FundOpenExchangeNavHistory
                return model, self._normalize_rows(fund, raw_rows, fetched_at=fetched_at)
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    retry_delay = min(2**attempt, 8)
                    fund_type = "货币基金" if fund.is_hb else "其他基金"
                    logger.warning(
                        f"基金 {fund.code}（{fund_type}）第 {attempt + 1}/{retries + 1} 次重试，{retry_delay} 秒后重试：{exc}"
                    )
                    await asyncio.sleep(retry_delay)
        assert last_error is not None
        raise last_error

    @staticmethod
    def _normalize_rows(
        fund: Fund,
        raw_rows: list[dict[str, Any]],
        *,
        fetched_at: datetime,
    ) -> list[dict[str, Any]]:
        """将东财字符串字段归一化，并补齐历史表公共字段。"""
        values: list[dict[str, Any]] = []
        for raw in raw_rows:
            data_date = normalize_date(raw.get("data_date"))
            common = {
                "fund_id": fund.id,
                "fund_code": fund.code,
                "data_date": data_date,
                "fetched_at": fetched_at,
            }
            if fund.is_hb:
                income_per_10k = normalize_decimal(raw.get("income_per_10k"))
                annualized_7d_pct = normalize_decimal(raw.get("annualized_7d_pct"))
                if income_per_10k is None and annualized_7d_pct is None:
                    continue
                values.append(
                    {
                        **common,
                        "income_per_10k": income_per_10k,
                        "annualized_7d_pct": annualized_7d_pct,
                    }
                )
                continue

            unit_nav = normalize_decimal(raw.get("unit_nav"))
            accumulated_nav = normalize_decimal(raw.get("accumulated_nav"))

            values.append(
                {
                    **common,
                    "unit_nav": unit_nav,
                    "accumulated_nav": accumulated_nav,
                    "daily_growth_pct": normalize_decimal(raw.get("daily_growth_pct")),
                }
            )
        values.sort(key=lambda row: row["data_date"])
        return values

    async def _upsert_history(self, model: HistoryModel, values: list[dict[str, Any]]) -> None:
        """按 ``fund_id, data_date`` 幂等写入历史记录。"""
        write_batches = list(iter_batches(values, size=HISTORY_UPSERT_BATCH_SIZE))
        for write_values in write_batches:
            statement = pg_insert(model).values(write_values)
            excluded_columns = {
                key
                for key in write_values[0]
                if key not in {"fund_id", "data_date", "created_at", "updated_at", "deleted_at"}
            }
            update_values = {column: getattr(statement.excluded, column) for column in excluded_columns}
            update_values.update({"updated_at": func.now(), "deleted_at": None})
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=[model.fund_id, model.data_date],
                    set_=update_values,
                )
            )
