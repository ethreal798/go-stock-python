"""全量基金目录同步。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund
from app.services.fund.common.utils import iter_batches
from app.services.fund.sources.catalog import (
    fetch_exchange_fund_codes,
    fetch_fund_catalog,
    fetch_money_fund_codes,
    fetch_open_fund_codes,
)

logger = logging.getLogger(__name__)


class FundCatalogSyncService:
    """将东方财富全量基金目录 upsert 到基金主表。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync(self) -> dict[str, int]:
        """同步入口：抓取全量基金并 upsert。

        核心逻辑：
        1. 主表：从三个数据源获取有效基金代码（决定哪些基金有效）
        2. 关联表：从 fundcode_search.js 获取基金详细信息（名称、类型）
        3. 用有效代码集合过滤，关联获取名称和类型
        """
        # 1. 主表：获取各类型基金代码集合
        money_codes = fetch_money_fund_codes()
        exchange_codes = fetch_exchange_fund_codes()
        open_codes = fetch_open_fund_codes()

        # 合并去重得到全量有效基金代码集合
        valid_codes = money_codes | exchange_codes | open_codes

        # 2. 关联表：从 fundcode_search.js 获取基金详细信息
        fund_catalog = fetch_fund_catalog()
        fund_catalog_map = {item["code"]: item for item in fund_catalog}

        # 3. 关联逻辑：用有效代码集合过滤，获取详细信息
        rows = []
        for code in valid_codes:
            info = fund_catalog_map.get(code, {"name": "", "type": ""})
            is_hb = code in money_codes
            is_exchange = code in exchange_codes

            rows.append({
                "code": code,
                "name": info.get("name", ""),
                "type": info.get("type", ""),
                "is_hb": is_hb,
                "is_exchange": is_exchange,
            })

        await self._upsert_funds(rows)

        counts = {"funds": len(rows)}
        logger.info("基金目录同步完成: %s", counts)
        return counts

    async def _upsert_funds(self, rows: list[dict[str, Any]]) -> None:
        for batch in iter_batches(rows, size=500):
            statement = pg_insert(Fund).values(batch)
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=[Fund.code],
                    set_={
                        "name": statement.excluded.name,
                        "type": statement.excluded.type,
                        "is_hb": statement.excluded.is_hb,
                        "is_exchange": statement.excluded.is_exchange,
                        "updated_at": func.now(),
                        "deleted_at": None,
                    },
                )
            )