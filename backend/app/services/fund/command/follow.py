"""用户关注基金写操作。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FollowedFund


class FundNotFoundError(LookupError):
    """目标基金不存在。"""


class FundFollowCommandService:
    """关注、取消关注及后续关注备注写操作。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def follow_fund(self, user_id: int, fund_code: str, remark: str | None = None) -> FollowedFund:
        fund = (await self.db.execute(select(Fund).where(Fund.code == fund_code))).scalar_one_or_none()
        if fund is None:
            raise FundNotFoundError(fund_code)

        statement = select(FollowedFund).where(
            FollowedFund.user_id == user_id,
            FollowedFund.fund_code == fund_code,
        )
        existing = (await self.db.execute(statement)).scalar_one_or_none()
        if existing is not None:
            return existing

        followed = FollowedFund(user_id=user_id, fund_code=fund_code, remark=remark)
        self.db.add(followed)
        await self.db.commit()
        await self.db.refresh(followed)
        return followed

    async def unfollow_fund(self, user_id: int, fund_code: str) -> bool:
        statement = select(FollowedFund).where(
            FollowedFund.user_id == user_id,
            FollowedFund.fund_code == fund_code,
        )
        record = (await self.db.execute(statement)).scalar_one_or_none()
        if record is None:
            return False
        await self.db.delete(record)
        await self.db.commit()
        return True
