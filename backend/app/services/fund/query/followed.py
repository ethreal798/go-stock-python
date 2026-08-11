"""用户关注基金列表读取服务。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import FollowedFund
from app.services.fund.query.catalog import FundCatalogQueryService


class FundFollowedQueryService:
    """读取用户关注记录及对应基金详情。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.catalog = FundCatalogQueryService(db)

    async def get_followed_funds(self, user_id: int) -> list[dict[str, Any]]:
        statement = select(FollowedFund).where(FollowedFund.user_id == user_id)
        records = (await self.db.execute(statement)).scalars().all()
        output = []
        for record in records:
            fund = await self.catalog.get_fund_detail(record.fund_code)
            if fund is not None:
                fund["is_followed"] = True
            output.append(
                {
                    "id": record.id,
                    "user_id": record.user_id,
                    "fund_code": record.fund_code,
                    "remark": record.remark,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "fund_info": fund,
                }
            )
        return output
