"""基金档案与风险指标最新值同步。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from math import ceil
from time import perf_counter
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundProfileLatest, FundRiskMetricLatest
from app.services.fund.common.formatter import format_fund_profile, format_fund_risk_metrics
from app.services.fund.common.utils import iter_batches, normalize_fund_code
from app.services.fund.sources.metadata import fetch_fund_profile_frame, fetch_fund_risk_frame

logger = logging.getLogger(__name__)


class FundMetadataSyncService:
    """按基金主表游标同步雪球档案与风险指标。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync(
        self,
        *,
        categories: Sequence[str] = ("open", "money", "exchange"),
        sync_profile: bool = True,
        sync_risk: bool = True,
        fund_codes: Sequence[str] | None = None,
        limit: int | None = None,
        concurrency: int = 4,
        batch_size: int = 20,
        retries: int = 2,
        timeout: float = 20,
    ) -> dict[str, int]:
        """同步最新档案和风险指标；无历史快照。"""
        selected_categories = tuple(dict.fromkeys(categories))
        unsupported = set(selected_categories) - {"open", "money", "exchange"}
        if unsupported:
            raise ValueError(f"不支持的基金分类: {sorted(unsupported)}")
        if not selected_categories or (not sync_profile and not sync_risk):
            return {"funds": 0, "profiles": 0, "risk_rows": 0, "failed": 0}
        if concurrency < 1 or batch_size < 1 or retries < 0 or timeout <= 0:
            raise ValueError("concurrency、batch_size、timeout 必须大于 0，retries 不能小于 0")
        if limit is not None and limit < 1:
            raise ValueError("limit 必须大于 0")

        normalized_codes = None
        if fund_codes:
            normalized_codes = [normalize_fund_code(code) for code in fund_codes]
        conditions = [Fund.status == "active", Fund.category.in_(selected_categories)]
        if normalized_codes:
            conditions.append(Fund.code.in_(normalized_codes))

        total = int((await self.db.execute(select(func.count(Fund.id)).where(*conditions))).scalar_one())
        target_total = min(total, limit) if limit is not None else total
        total_batches = ceil(target_total / batch_size) if target_total else 0
        sync_id = uuid4().hex[:8]
        started_at = perf_counter()
        semaphore = asyncio.Semaphore(concurrency)
        result = {"funds": 0, "profiles": 0, "risk_rows": 0, "failed": 0}
        last_id = 0
        batch_index = 0

        logger.info(
            "event=fund_metadata_sync.started sync_id=%s categories=%s profile=%s risk=%s "
            "source_total=%s target_total=%s total_batches=%s batch_size=%s concurrency=%s retries=%s",
            sync_id,
            selected_categories,
            sync_profile,
            sync_risk,
            total,
            target_total,
            total_batches,
            batch_size,
            concurrency,
            retries,
        )

        while result["funds"] < target_total:
            current_size = min(batch_size, target_total - result["funds"])
            statement = select(Fund).where(*conditions, Fund.id > last_id).order_by(Fund.id).limit(current_size)
            funds = list((await self.db.execute(statement)).scalars().all())
            if not funds:
                logger.warning(
                    "event=fund_metadata_sync.cursor_exhausted sync_id=%s processed=%s target_total=%s last_id=%s",
                    sync_id,
                    result["funds"],
                    target_total,
                    last_id,
                )
                break
            batch_index += 1
            batch_started_at = perf_counter()
            last_id = funds[-1].id
            logger.info(
                "event=fund_metadata_sync.batch_started sync_id=%s batch=%s/%s size=%s first_fund=%s last_fund=%s",
                sync_id,
                batch_index,
                total_batches,
                len(funds),
                funds[0].code,
                funds[-1].code,
            )
            responses = await asyncio.gather(
                *[
                    self._sync_one(
                        fund,
                        sync_profile=sync_profile,
                        sync_risk=sync_risk,
                        semaphore=semaphore,
                        retries=retries,
                        timeout=timeout,
                        sync_id=sync_id,
                        batch_index=batch_index,
                    )
                    for fund in funds
                ]
            )
            profiles: list[dict[str, Any]] = []
            risk_rows: list[dict[str, Any]] = []
            for fund, response in zip(funds, responses):
                result["funds"] += 1
                for error in response["errors"]:
                    result["failed"] += 1
                    logger.warning(
                        "event=fund_metadata_sync.fund_failed sync_id=%s batch=%s/%s fund=%s "
                        "category=%s content=%s error_type=%s error=%s",
                        sync_id,
                        batch_index,
                        total_batches,
                        fund.code,
                        fund.category,
                        error["content"],
                        type(error["exception"]).__name__,
                        error["exception"],
                    )
                if response["profile"] is not None:
                    profiles.append({**response["profile"], "fund_id": fund.id})
                risk_rows.extend({**row, "fund_id": fund.id} for row in response["risks"])

            if profiles:
                await self._upsert_latest(FundProfileLatest, profiles, ["fund_id"])
            if risk_rows:
                await self._upsert_latest(FundRiskMetricLatest, risk_rows, ["fund_id", "period"])
            await self.db.commit()
            result["profiles"] += len(profiles)
            result["risk_rows"] += len(risk_rows)
            logger.info(
                "event=fund_metadata_sync.batch_committed sync_id=%s batch=%s/%s processed=%s/%s "
                "profiles=%s risk_rows=%s failed=%s elapsed_seconds=%.2f",
                sync_id,
                batch_index,
                total_batches,
                result["funds"],
                target_total,
                len(profiles),
                len(risk_rows),
                result["failed"],
                perf_counter() - batch_started_at,
            )

        logger.info(
            "event=fund_metadata_sync.completed sync_id=%s processed=%s target_total=%s profiles=%s "
            "risk_rows=%s failed=%s elapsed_seconds=%.2f",
            sync_id,
            result["funds"],
            target_total,
            result["profiles"],
            result["risk_rows"],
            result["failed"],
            perf_counter() - started_at,
        )
        return result

    async def _sync_one(
        self,
        fund: Fund,
        *,
        sync_profile: bool,
        sync_risk: bool,
        semaphore: asyncio.Semaphore,
        retries: int,
        timeout: float,
        sync_id: str,
        batch_index: int,
    ) -> dict[str, Any] | None:
        async with semaphore:
            response: dict[str, Any] = {"profile": None, "risks": [], "errors": []}
            if sync_profile:
                try:
                    response["profile"] = await self._fetch_profile(fund.code, retries, timeout, sync_id, batch_index)
                except Exception as exc:
                    response["errors"].append({"content": "profile", "exception": exc})
            # 雪球不为货币基金提供这组风险分析，正常跳过而不是记失败。
            if sync_risk and fund.category != "money":
                try:
                    response["risks"] = await self._fetch_risk(fund.code, retries, timeout, sync_id, batch_index)
                except Exception as exc:
                    response["errors"].append({"content": "risk", "exception": exc})
            return response

    async def _fetch_profile(
        self, fund_code: str, retries: int, timeout: float, sync_id: str, batch_index: int
    ) -> dict[str, Any] | None:
        for attempt in range(retries + 1):
            try:
                fetched_at = datetime.now()
                frame = await asyncio.to_thread(fetch_fund_profile_frame, fund_code, timeout=timeout)
                if len(getattr(frame, "columns", [])) == 0 or len(frame) == 0:
                    return None
                return format_fund_profile(frame, fund_code=fund_code, fetched_at=fetched_at)
            except Exception:
                if attempt == retries:
                    raise
                await self._retry_delay(sync_id, batch_index, fund_code, "profile", attempt, retries)
        raise AssertionError("unreachable")

    async def _fetch_risk(
        self, fund_code: str, retries: int, timeout: float, sync_id: str, batch_index: int
    ) -> list[dict[str, Any]]:
        for attempt in range(retries + 1):
            try:
                fetched_at = datetime.now()
                frame = await asyncio.to_thread(fetch_fund_risk_frame, fund_code, timeout=timeout)
                return format_fund_risk_metrics(frame, fund_code=fund_code, fetched_at=fetched_at)
            except Exception:
                if attempt == retries:
                    raise
                await self._retry_delay(sync_id, batch_index, fund_code, "risk", attempt, retries)
        raise AssertionError("unreachable")

    @staticmethod
    async def _retry_delay(
        sync_id: str, batch_index: int, fund_code: str, content: str, attempt: int, retries: int
    ) -> None:
        delay = min(2**attempt, 8)
        logger.warning(
            "event=fund_metadata_sync.fund_retrying sync_id=%s batch=%s fund=%s content=%s "
            "attempt=%s/%s retry_delay_seconds=%s",
            sync_id,
            batch_index,
            fund_code,
            content,
            attempt + 1,
            retries + 1,
            delay,
            exc_info=True,
        )
        await asyncio.sleep(delay)

    async def _upsert_latest(self, model: type, values: list[dict[str, Any]], conflict_columns: list[str]) -> None:
        for batch in iter_batches(values):
            statement = pg_insert(model).values(batch)
            excluded_columns = {
                key for key in batch[0] if key not in {*conflict_columns, "created_at", "updated_at", "deleted_at"}
            }
            update_values = {column: getattr(statement.excluded, column) for column in excluded_columns}
            update_values.update({"updated_at": func.now(), "deleted_at": None})
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=[getattr(model, column) for column in conflict_columns],
                    set_=update_values,
                )
            )
