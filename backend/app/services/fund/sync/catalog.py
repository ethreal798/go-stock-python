"""全量基金目录同步。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund
from app.services.fund.common.utils import iter_batches
from app.services.fund.sources.catalog import fetch_fund_catalog

logger = logging.getLogger(__name__)


class FundCatalogSyncService:
    """将东方财富全量基金目录 upsert 到基金主表。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_and_sync(self) -> dict[str, int]:
        """同步入口：抓取全量基金并 upsert。"""
        rows = fetch_fund_catalog()
        if not rows:
            logger.warning("基金目录为空，跳过同步")
            return {"funds": 0}

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
                        "updated_at": func.now(),
                        "deleted_at": None,
                    },
                )
            )