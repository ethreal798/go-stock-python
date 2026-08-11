"""用户基金自选列表读取服务。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import FundWatchlistItem
from app.services.fund.query.catalog import FundCatalogQueryService


class FundWatchlistQueryService:
    """读取用户自选项及对应基金详情。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.catalog = FundCatalogQueryService(db)

    async def get_watchlist(self, user_id: int) -> list[dict[str, Any]]:
        statement = select(FundWatchlistItem).where(FundWatchlistItem.user_id == user_id)
        items = (await self.db.execute(statement)).scalars().all()
        output = []
        for item in items:
            fund = await self.catalog.get_fund_detail(item.fund_code)
            if fund is not None:
                fund["is_in_watchlist"] = True
            output.append(
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "fund_code": item.fund_code,
                    "remark": item.remark,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "fund_info": fund,
                }
            )
        return output
