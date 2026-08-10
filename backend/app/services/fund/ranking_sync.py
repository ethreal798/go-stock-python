"""东方财富三个基金排行接口的标准化与最新快照入库。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundExchangeRankLatest, FundMoneyRankLatest, FundOpenRankLatest
from app.services.fund.formatter import format_exchange_rank, format_money_rank, format_open_rank
from app.services.fund.history_sync import FundHistorySyncService
from app.services.fund.utils import iter_batches

logger = logging.getLogger(__name__)


def build_fund_candidates(
    open_rows: list[dict[str, Any]],
    exchange_rows: list[dict[str, Any]],
    money_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """以 money > open > exchange 的路由优先级反推基金主表。"""
    candidates: dict[str, dict[str, Any]] = {}
    for category, rows in (("exchange", exchange_rows), ("open", open_rows), ("money", money_rows)):
        for row in rows:
            code = row["fund_code"]
            previous = candidates.get(code)
            raw_type = row.get("fund_type")
            # 如果当前处理的是 open 类别，且该代码之前已经在 exchange 中出现过，且之前的类型包含 “LOF”，那么强制沿用之前的类型 (“LOF”)。
            if category == "open" and previous and previous.get("type") and "LOF" in previous["type"].upper():
                raw_type = previous["type"]
            candidates[code] = {
                "code": code,
                "name": row["fund_name"],
                # 使用 raw_type or ... 的逻辑：如果当前数据源没有提供具体类型，则根据 category 提供一个默认类型。
                "type": raw_type or {"open": "开放式基金", "money": "货币型基金"}.get(category, "场内交易基金"),
                "category": category,
                "status": "active",
                "last_seen_data_date": row["data_date"],
                "last_seen_at": row["fetched_at"],
                "deleted_at": None,
            }
    return candidates


async def fetch_rank_frames() -> tuple[Any, Any, Any]:
    """依次调用三个同步 AKShare 接口，规避其排行解析过程的并发不安全。"""
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("缺少 akshare，请先执行 pip install -r requirements.txt") from exc

    return (
        await asyncio.to_thread(ak.fund_open_fund_rank_em, symbol="全部"),
        await asyncio.to_thread(ak.fund_exchange_rank_em),
        await asyncio.to_thread(ak.fund_money_rank_em),
    )


class FundRankingSyncService:
    """三个排行全部校验通过后，在同一数据库事务内更新主表和快照。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync(self) -> dict[str, int]:
        """同步入口"""
        # 1.抓取东财基金排行数据
        open_frame, exchange_frame, money_frame = await fetch_rank_frames()
        # 2.格式化数据
        fetched_at = datetime.now()
        open_rows = format_open_rank(open_frame, fetched_at, minimum_rows=1000)
        exchange_rows = format_exchange_rank(exchange_frame, fetched_at, minimum_rows=100)
        money_rows = format_money_rank(money_frame, fetched_at, minimum_rows=100)
        # 3.存储入库
        return await self.save(open_rows, exchange_rows, money_rows)

    async def save(
        self,
        open_rows: list[dict[str, Any]],
        exchange_rows: list[dict[str, Any]],
        money_rows: list[dict[str, Any]],
    ) -> dict[str, int]:
        # 1. 构建基金主表
        candidates = build_fund_candidates(open_rows, exchange_rows, money_rows)
        all_codes = sorted(candidates)
        await self._upsert_funds(list(candidates.values()))

        # 2. 判断写入基金主表是否正确
        result = await self.db.execute(select(Fund.id, Fund.code).where(Fund.code.in_(all_codes)))
        fund_ids = {code: fund_id for fund_id, code in result.all()}
        if len(fund_ids) != len(all_codes):
            missing = sorted(set(all_codes) - set(fund_ids))
            raise RuntimeError(f"基金主表写入不完整，缺少代码: {missing[:10]}")

        # 3. 将各个类型排行榜数据进行入库
        await self._replace_latest(FundOpenRankLatest, open_rows, fund_ids)
        await self._replace_latest(FundExchangeRankLatest, exchange_rows, fund_ids)
        await self._replace_latest(FundMoneyRankLatest, money_rows, fund_ids)
        history_counts = await FundHistorySyncService(self.db).append_rank_snapshots(
            open_rows, exchange_rows, money_rows, fund_ids
        )
        # 4. 将本次未更新的基金状态设置为 stale
        await self.db.execute(update(Fund).where(Fund.code.not_in(all_codes)).values(status="stale"))

        # 5. 统计本次抓取结果
        counts = {
            "funds": len(all_codes),
            "open": len(open_rows),
            "exchange": len(exchange_rows),
            "money": len(money_rows),
            "history_open_rows": history_counts["open_rows"],
            "history_exchange_rows": history_counts["exchange_rows"],
            "history_money_rows": history_counts["money_rows"],
        }
        logger.info("基金排行同步完成: %s", counts)
        return counts

    async def _upsert_funds(self, rows: list[dict[str, Any]]) -> None:
        """更新基金主表数据 如基金类型 状态（活跃/停止购买）"""
        for batch in iter_batches(rows):
            # pg_insert(Fund): 导入并使用 PostgreSQL 特定的 insert 语法（通常来自 sqlalchemy.dialects.postgresql）
            # 因为标准的 SQL INSERT 语法在处理冲突更新（ON CONFLICT）时功能有限。
            # .values(batch): 将当前批次的数据填充到 SQL 语句中。此时 statement 代表一个标准的 INSERT INTO Fund ... VALUES ... 语句。
            statement = pg_insert(Fund).values(batch)
            # 执行带冲突解决的 SQL
            await self.db.execute(
                # .on_conflict_do_update(...): 这是 PostgreSQL 的核心语法（类似 MySQL 的 ON DUPLICATE KEY UPDATE）。
                # 它定义了当插入遇到主键或唯一索引冲突时（即基金代码已存在），该如何处理。这里是转为更新操作。
                statement.on_conflict_do_update(
                    index_elements=[Fund.code],  # 指定判定冲突的依据是 Fund.code（基金代码）字段。
                    set_={
                        "name": statement.excluded.name,
                        # 保留已经存在的细类型（例如 LOF/混合型），仅在原值为空时补通用类型。
                        "type": func.coalesce(Fund.type, statement.excluded.type),
                        "category": statement.excluded.category,
                        "status": "active",
                        "last_seen_data_date": statement.excluded.last_seen_data_date,
                        "last_seen_at": statement.excluded.last_seen_at,
                        "deleted_at": None,
                        "updated_at": statement.excluded.last_seen_at,
                    },
                )
            )

    async def _replace_latest(
        self,
        model: type[FundOpenRankLatest] | type[FundExchangeRankLatest] | type[FundMoneyRankLatest],
        rows: list[dict[str, Any]],
        fund_ids: dict[str, int],
    ) -> None:
        """全量替换并同步特定的基金排行榜表并清理那些不在新数据中的旧记录"""
        values = [{**row, "fund_id": fund_ids[row["fund_code"]]} for row in rows]
        update_columns = [key for key in values[0] if key not in {"fund_code", "created_at"}]
        # 分批 Upsert（插入或更新）
        for batch in iter_batches(values):
            statement = pg_insert(model).values(batch)
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=[model.fund_code],
                    set_={column: getattr(statement.excluded, column) for column in update_columns},
                )
            )
        # 数据清理（删除过时记录）
        current_codes = [row["fund_code"] for row in rows]
        await self.db.execute(delete(model).where(model.fund_code.not_in(current_codes)))
