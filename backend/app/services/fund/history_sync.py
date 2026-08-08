"""开放式/LOF、场内 ETF 净值与货币基金收益历史同步。"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from math import ceil
from time import perf_counter
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundExchangeNavHistory, FundMoneyYieldHistory, FundOpenNavHistory
from app.services.fund.formatter import (
    format_exchange_nav_history,
    format_money_yield_history,
    format_open_nav_history,
)
from app.services.fund.history_source import fetch_exchange_nav_frame, fetch_money_yield_frame, fetch_open_nav_frames
from app.services.fund.utils import iter_batches, normalize_fund_code

logger = logging.getLogger(__name__)

HISTORY_UPSERT_BATCH_SIZE = 500


def three_years_before(value: date) -> date:
    """返回以自然年计算的三年前日期，兼容 2 月 29 日。"""
    # 如果当天是闰年的2月29日，直接减3年可能遇到平年（只有2月28日），导致 ValueError。
    # 通过 try-except 捕获这种情况，并回退到2月28日，保证计算结果有效。
    try:
        return value.replace(year=value.year - 3)
    except ValueError:
        return value.replace(year=value.year - 3, month=2, day=28)


class FundHistorySyncService:
    """按基金主表分类回补历史，批次提交以支持中断后幂等重跑。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync(
        self,
        *,
        categories: Sequence[str] = ("open", "money", "exchange"),
        start_date: date | None = None,
        end_date: date | None = None,
        fund_codes: Sequence[str] | None = None,
        limit: int | None = None,
        concurrency: int = 4,
        batch_size: int = 20,
        retries: int = 2,
    ) -> dict[str, int]:
        """同步指定分类近三年历史，返回基金数、写入行数和失败数。"""
        sync_id = uuid4().hex[:8]
        sync_started_at = perf_counter()
        # 1. 使用 dict.fromkeys 去除 categories 列表中的重复项，同时保持顺序。
        selected_categories = tuple(dict.fromkeys(categories))
        unsupported = set(selected_categories) - {"open", "money", "exchange"}
        if unsupported:
            raise ValueError(f"不支持的基金分类: {sorted(unsupported)}")
        if not selected_categories:
            return {"funds": 0, "rows": 0, "failed": 0}
        # 2. 校验 concurrency（并发数）、batch_size（批大小）等参数的合法性。
        if concurrency < 1 or batch_size < 1 or retries < 0:
            raise ValueError("concurrency、batch_size 必须大于 0，retries 不能小于 0")

        # 3. 自动解析日期：如果未指定 start_date，默认调用 three_years_before 从 end_date（默认今天）往前推3年。
        resolved_end = end_date or date.today()
        resolved_start = start_date or three_years_before(resolved_end)
        if resolved_start > resolved_end:
            raise ValueError("start_date 不能晚于 end_date")

        # 4. 提取基金代码
        normalized_codes = None
        if fund_codes:
            normalized_codes = [normalize_fund_code(code) for code in fund_codes]

        # 5. 从基金主表中匹配状态为活跃且类型涵盖 open or money 的基金。
        conditions = [Fund.status == "active", Fund.category.in_(selected_categories)]
        if normalized_codes:
            conditions.append(Fund.code.in_(normalized_codes))
        if limit is not None:
            if limit < 1:
                raise ValueError("limit 必须大于 0")

        total = int((await self.db.execute(select(func.count(Fund.id)).where(*conditions))).scalar_one())
        target_total = min(total, limit) if limit is not None else total
        total_batches = ceil(target_total / batch_size) if target_total else 0
        semaphore = asyncio.Semaphore(concurrency)
        result = {"funds": 0, "rows": 0, "failed": 0}
        last_id = 0
        batch_index = 0

        logger.info(
            "event=fund_history_sync.started sync_id=%s categories=%s start=%s end=%s "
            "source_total=%s target_total=%s total_batches=%s batch_size=%s concurrency=%s retries=%s "
            "code_filter=%s limit=%s",
            sync_id,
            selected_categories,
            resolved_start,
            resolved_end,
            total,
            target_total,
            total_batches,
            batch_size,
            concurrency,
            retries,
            len(normalized_codes) if normalized_codes else "all",
            limit,
        )

        if target_total == 0:
            logger.info("event=fund_history_sync.empty sync_id=%s reason=no_matching_active_funds", sync_id)
            return result

        # 6. 使用主键游标分页。batch_size 只决定每批数量，不会截断后续基金。
        while result["funds"] < target_total:
            batch_index += 1
            batch_started_at = perf_counter()
            # 动态批次大小计算
            current_batch_size = min(batch_size, target_total - result["funds"])
            # 每次查询都从上次结束的位置（ID）继续往下查，确保所有符合条件的基金都能被遍历到，不会遗漏，也不会重复。
            stmt = select(Fund).where(*conditions, Fund.id > last_id).order_by(Fund.id).limit(current_batch_size)
            # 自动终止机制 如果因为并发环境下，实际获取到的数量可能因为各种原因（比如数据刚好被删了）少于预期。如果查不到结果，直接跳出循环，防止死循环。
            fund_batch = list((await self.db.execute(stmt)).scalars().all())
            if not fund_batch:
                logger.warning(
                    "event=fund_history_sync.cursor_exhausted sync_id=%s processed=%s target_total=%s last_id=%s",
                    sync_id,
                    result["funds"],
                    target_total,
                    last_id,
                )
                break
            # 更新最后一条基金id
            last_id = fund_batch[-1].id
            category_counts = {
                category: sum(1 for fund in fund_batch if fund.category == category) for category in selected_categories
            }
            logger.info(
                "event=fund_history_sync.batch_started sync_id=%s batch=%s/%s size=%s "
                "first_fund=%s last_fund=%s categories=%s",
                sync_id,
                batch_index,
                total_batches,
                len(fund_batch),
                fund_batch[0].code,
                fund_batch[-1].code,
                category_counts,
            )

            # tasks 是一个“待办事项”的列表（协程对象集合），它们只是代表了“即将要执行的操作”，还没有真正开始跑（或者刚刚开始但在等待）。
            tasks = [
                # 调用 self._sync_one(...) 时（注意没有 await），Python 不会执行函数体里的代码。而是创建了一个协程对象。
                self._sync_one(
                    fund,
                    category=fund.category,
                    start_date=resolved_start,
                    end_date=resolved_end,
                    semaphore=semaphore,
                    retries=retries,
                    sync_id=sync_id,
                    batch_index=batch_index,
                )
                for fund in fund_batch
            ]
            # asyncio.gather阻塞当前流程，直到 tasks 列表里的所有任务都执行完毕（无论成功还是失败）。
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            values_by_category: dict[str, list[dict[str, Any]]] = {
                category: [] for category in selected_categories
            }
            batch_failed = 0
            # fund_batch 和 responses 是两个独立的列表。如果用索引去写（比如 for i in range(len): fund = fund_batch[i]...），代码会很丑且容易出错。
            # 用了 zip，你可以直接在循环里同时拿到“我是谁（fund）”和“我干得怎么样”。
            for fund, response in zip(fund_batch, responses):
                result["funds"] += 1
                if isinstance(response, Exception):
                    result["failed"] += 1
                    batch_failed += 1
                    logger.warning(
                        "event=fund_history_sync.fund_failed sync_id=%s batch=%s/%s fund=%s "
                        "category=%s error_type=%s error=%s",
                        sync_id,
                        batch_index,
                        total_batches,
                        fund.code,
                        fund.category,
                        type(response).__name__,
                        response,
                    )
                    continue
                # 将基金的抓取结果分类放入values_by_category字典
                values_by_category[fund.category].extend(
                    {**row, "fund_id": fund.id, "fund_code": fund.code} for row in response
                )

            batch_rows = sum(len(values) for values in values_by_category.values())
            logger.info(
                "event=fund_history_sync.batch_fetched sync_id=%s batch=%s/%s success=%s failed=%s "
                "open_rows=%s money_rows=%s exchange_rows=%s elapsed_seconds=%.2f",
                sync_id,
                batch_index,
                total_batches,
                len(fund_batch) - batch_failed,
                batch_failed,
                len(values_by_category.get("open", [])),
                len(values_by_category.get("money", [])),
                len(values_by_category.get("exchange", [])),
                perf_counter() - batch_started_at,
            )

            for category, values in values_by_category.items():
                if not values:
                    continue
                model_by_category = {
                    "open": FundOpenNavHistory,
                    "money": FundMoneyYieldHistory,
                    "exchange": FundExchangeNavHistory,
                }
                model = model_by_category[category]
                logger.info(
                    "event=fund_history_sync.persist_started sync_id=%s batch=%s/%s category=%s rows=%s",
                    sync_id,
                    batch_index,
                    total_batches,
                    category,
                    len(values),
                )
                try:
                    await self._upsert_history(model, values)
                except Exception:
                    logger.exception(
                        "event=fund_history_sync.persist_failed sync_id=%s batch=%s/%s category=%s rows=%s",
                        sync_id,
                        batch_index,
                        total_batches,
                        category,
                        len(values),
                    )
                    raise
                result["rows"] += len(values)
                logger.info(
                    "event=fund_history_sync.persist_completed sync_id=%s batch=%s/%s category=%s rows=%s",
                    sync_id,
                    batch_index,
                    total_batches,
                    category,
                    len(values),
                )

            # 每批提交，网络中断时已完成批次可以直接重跑而不会重复插入。
            try:
                await self.db.commit()
            except Exception:
                logger.exception(
                    "event=fund_history_sync.commit_failed sync_id=%s batch=%s/%s processed=%s/%s",
                    sync_id,
                    batch_index,
                    total_batches,
                    result["funds"],
                    target_total,
                )
                raise
            logger.info(
                "event=fund_history_sync.batch_committed sync_id=%s batch=%s/%s processed=%s/%s "
                "batch_rows=%s total_rows=%s total_failed=%s last_fund=%s elapsed_seconds=%.2f",
                sync_id,
                batch_index,
                total_batches,
                result["funds"],
                target_total,
                batch_rows,
                result["rows"],
                result["failed"],
                fund_batch[-1].code,
                perf_counter() - batch_started_at,
            )

        elapsed_seconds = perf_counter() - sync_started_at
        logger.info(
            "event=fund_history_sync.completed sync_id=%s categories=%s start=%s end=%s "
            "processed=%s target_total=%s rows=%s failed=%s elapsed_seconds=%.2f funds_per_second=%.2f",
            sync_id,
            selected_categories,
            resolved_start,
            resolved_end,
            result["funds"],
            target_total,
            result["rows"],
            result["failed"],
            elapsed_seconds,
            result["funds"] / elapsed_seconds if elapsed_seconds else 0,
        )
        return result

    async def _sync_one(
        self,
        fund: Fund,
        *,
        category: str,
        start_date: date,
        end_date: date,
        semaphore: asyncio.Semaphore,
        retries: int,
        sync_id: str,
        batch_index: int,
    ) -> list[dict[str, Any]]:
        # 1. 并发控制：信号量 假设 concurrency=4，那么同一时刻只有 4 个 _sync_one 协程能通过这行代码进入执行体。
        async with semaphore:
            fund_started_at = perf_counter()
            last_error: Exception | None = None
            for attempt in range(retries + 1):
                logger.debug(
                    "event=fund_history_sync.fund_fetch_started sync_id=%s batch=%s fund=%s "
                    "category=%s attempt=%s/%s",
                    sync_id,
                    batch_index,
                    fund.code,
                    category,
                    attempt + 1,
                    retries + 1,
                )
                try:
                    fetched_at = datetime.now()
                    # 分类型调用对应的抓取方法以及格式化方法
                    if category == "open":
                        # asyncio.to_thread将阻塞的函数 fetch_open_nav_frames 放到一个独立的线程池中运行，主协程在这里挂起，等待线程池返回结果。
                        unit_frame, accumulated_frame = await asyncio.to_thread(fetch_open_nav_frames, fund.code)
                        rows = format_open_nav_history(
                            unit_frame,
                            accumulated_frame,
                            start_date=start_date,
                            end_date=end_date,
                            fetched_at=fetched_at,
                        )
                    elif category == "money":
                        frame = await asyncio.to_thread(
                            fetch_money_yield_frame,
                            fund.code,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        rows = format_money_yield_history(
                            frame,
                            start_date=start_date,
                            end_date=end_date,
                            fetched_at=fetched_at,
                        )
                    else:
                        frame = await asyncio.to_thread(
                            fetch_exchange_nav_frame,
                            fund.code,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        rows = format_exchange_nav_history(
                            frame,
                            start_date=start_date,
                            end_date=end_date,
                            fetched_at=fetched_at,
                        )
                    logger.debug(
                        "event=fund_history_sync.fund_fetch_succeeded sync_id=%s batch=%s fund=%s "
                        "category=%s rows=%s elapsed_seconds=%.2f",
                        sync_id,
                        batch_index,
                        fund.code,
                        category,
                        len(rows),
                        perf_counter() - fund_started_at,
                    )
                    return rows
                except Exception as exc:  # 网络、数据源字段和单只基金异常均隔离处理
                    last_error = exc
                    if attempt < retries:
                        retry_delay = min(2**attempt, 8)
                        logger.warning(
                            "event=fund_history_sync.fund_retrying sync_id=%s batch=%s fund=%s "
                            "category=%s attempt=%s/%s retry_delay_seconds=%s error_type=%s error=%s",
                            sync_id,
                            batch_index,
                            fund.code,
                            category,
                            attempt + 1,
                            retries + 1,
                            retry_delay,
                            type(exc).__name__,
                            exc,
                        )
                        await asyncio.sleep(retry_delay)  # 指数退避
            assert last_error is not None
            raise last_error

    async def _upsert_history(
        self,
        model: type[FundOpenNavHistory] | type[FundMoneyYieldHistory] | type[FundExchangeNavHistory],
        values: list[dict[str, Any]],
    ) -> None:
        # 20 只基金的三年历史可能产生九万多个绑定参数，超过 PostgreSQL/asyncpg
        # 单条语句的参数上限，因此数据库写入需要在基金抓取批次内再次分片。
        write_batches = list(iter_batches(values, size=HISTORY_UPSERT_BATCH_SIZE))
        for write_index, write_values in enumerate(write_batches, start=1):
            statement = pg_insert(model).values(write_values)
            excluded_columns = {
                key
                for key in write_values[0]
                if key not in {"fund_id", "data_date", "created_at", "updated_at", "deleted_at"}
            }
            update_values = {column: getattr(statement.excluded, column) for column in excluded_columns}
            update_values.update({"updated_at": func.now(), "deleted_at": None})
            logger.debug(
                "event=fund_history_sync.upsert_chunk model=%s chunk=%s/%s rows=%s",
                model.__tablename__,
                write_index,
                len(write_batches),
                len(write_values),
            )
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=[model.fund_id, model.data_date],
                    set_=update_values,
                )
            )

    async def append_rank_snapshots(
        self,
        open_rows: list[dict[str, Any]],
        exchange_rows: list[dict[str, Any]],
        money_rows: list[dict[str, Any]],
        fund_ids: dict[str, int],
    ) -> dict[str, int]:
        """把排行同步已经取得的最新值追加到历史表。

        货币排行没有申购/赎回状态，因此这里不携带状态字段，避免每日排行
        快照把历史接口已保存的状态覆盖成空值。排行存在交集时沿用主表的
        money > open > exchange 路由优先级，确保 LOF 不会写入场内历史表。
        """
        money_codes = {row["fund_code"] for row in money_rows}
        open_codes = {row["fund_code"] for row in open_rows} - money_codes
        exchange_codes = {row["fund_code"] for row in exchange_rows} - open_codes - money_codes
        open_values = [
            {
                "fund_id": fund_ids[row["fund_code"]],
                "fund_code": row["fund_code"],
                "data_date": row["data_date"],
                "unit_nav": row.get("unit_nav"),
                "accumulated_nav": row.get("accumulated_nav"),
                "daily_growth_pct": row.get("daily_growth_pct"),
                "fetched_at": row["fetched_at"],
            }
            for row in open_rows
            if row.get("data_date") is not None
            and row["fund_code"] in fund_ids
            and row["fund_code"] in open_codes
        ]
        money_values = [
            {
                "fund_id": fund_ids[row["fund_code"]],
                "fund_code": row["fund_code"],
                "data_date": row["data_date"],
                "income_per_10k": row.get("income_per_10k"),
                "annualized_7d_pct": row.get("annualized_7d_pct"),
                "fetched_at": row["fetched_at"],
            }
            for row in money_rows
            if row.get("data_date") is not None
            and row["fund_code"] in fund_ids
            and row["fund_code"] in money_codes
        ]
        exchange_values = [
            {
                "fund_id": fund_ids[row["fund_code"]],
                "fund_code": row["fund_code"],
                "data_date": row["data_date"],
                "unit_nav": row.get("unit_nav"),
                "accumulated_nav": row.get("accumulated_nav"),
                # 场内排行不提供日增长率和申赎状态，不写这些键，避免覆盖历史详情。
                "fetched_at": row["fetched_at"],
            }
            for row in exchange_rows
            if row.get("data_date") is not None
            and row["fund_code"] in fund_ids
            and row["fund_code"] in exchange_codes
        ]
        if open_values:
            await self._upsert_history(FundOpenNavHistory, open_values)
        if money_values:
            await self._upsert_history(FundMoneyYieldHistory, money_values)
        if exchange_values:
            await self._upsert_history(FundExchangeNavHistory, exchange_values)
        return {
            "open_rows": len(open_values),
            "money_rows": len(money_values),
            "exchange_rows": len(exchange_values),
        }
