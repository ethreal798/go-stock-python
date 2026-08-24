"""用户基金自选写操作。"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundWatchlistItem


class FundNotFoundError(LookupError):
    """目标基金不存在。"""


class FundWatchlistCommandService:
    """加入自选、移出自选及自选备注写操作。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_to_watchlist(
        self,
        user_id: int,
        fund_code: str,
        remark: str | None = None,
    ) -> FundWatchlistItem:
        fund = (await self.db.execute(select(Fund).where(Fund.code == fund_code))).scalar_one_or_none()
        if fund is None:
            raise FundNotFoundError(fund_code)

        statement = select(FundWatchlistItem).where(
            FundWatchlistItem.user_id == user_id,
            FundWatchlistItem.fund_code == fund_code,
        )
        existing = (await self.db.execute(statement)).scalar_one_or_none()
        if existing is not None:
            return existing

        item = FundWatchlistItem(user_id=user_id, fund_code=fund_code, remark=remark)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_from_watchlist(self, user_id: int, fund_code: str) -> bool:
        statement = select(FundWatchlistItem).where(
            FundWatchlistItem.user_id == user_id,
            FundWatchlistItem.fund_code == fund_code,
        )
        item = (await self.db.execute(statement)).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="基金自选记录不存在")
        await self.db.delete(item)
        await self.db.commit()
