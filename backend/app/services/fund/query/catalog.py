"""基金目录、搜索和详情读取服务。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FundExchangeRankLatest, FundMoneyRankLatest, FundOpenRankLatest, FundWatchlistItem


class FundCatalogQueryService:
    """读取基金身份和对应分类的最新排行指标。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_fund_detail(self, code: str) -> dict[str, Any] | None:
        statement = self._fund_with_latest_query().where(Fund.code == code)
        row = (await self.db.execute(statement)).one_or_none()
        if row is None:
            return None
        return self._fund_payload(*row)

    async def search_funds(
        self,
        keyword: str,
        limit: int = 20,
        page: int = 1,
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        contains_pattern = f"%{keyword}%"
        prefix_pattern = f"{keyword}%"

        # 第一步：只在基金主表中完成筛选、排序和分页
        fund_page = (
            select(Fund)
            .where(
                or_(
                    Fund.code.ilike(contains_pattern),
                    Fund.name.ilike(contains_pattern),
                ),
            )
            .order_by(
                Fund.code.ilike(prefix_pattern).desc(),
                Fund.name.ilike(prefix_pattern).desc(),
                Fund.code,
            )
            .limit(limit)
            .offset((page - 1) * limit)
            .subquery()
        )

        page_fund = aliased(Fund, fund_page)

        # 第二步：只为这一页基金关联 latest_rank
        statement = self._fund_with_latest_query(page_fund).order_by(
            page_fund.code.ilike(prefix_pattern).desc(),
            page_fund.name.ilike(prefix_pattern).desc(),
            page_fund.code,
        )

        rows = list((await self.db.execute(statement)).all())
        watchlist_codes = await self._watchlist_codes(user_id)
        return [self._fund_payload(*row, is_in_watchlist=row[0].code in watchlist_codes) for row in rows]

    async def _watchlist_codes(self, user_id: int | None) -> set[str]:
        """查询当前用户的基金自选代码。"""
        if user_id is None:
            return set()
        statement = select(FundWatchlistItem.fund_code).where(FundWatchlistItem.user_id == user_id)
        return set((await self.db.execute(statement)).scalars().all())

    @staticmethod
    def _fund_with_latest_query(fund_source=Fund):
        return (
            select(fund_source, FundOpenRankLatest, FundExchangeRankLatest, FundMoneyRankLatest)
            .select_from(fund_source)
            .outerjoin(FundOpenRankLatest, FundOpenRankLatest.fund_id == fund_source.id)
            .outerjoin(FundExchangeRankLatest, FundExchangeRankLatest.fund_id == fund_source.id)
            .outerjoin(FundMoneyRankLatest, FundMoneyRankLatest.fund_id == fund_source.id)
        )

    @staticmethod
    def _latest_payload(open_rank, exchange_rank, money_rank, category: str) -> dict[str, Any] | None:
        """根据基金类型组装其相关字段数据  目前纳入范围 场内/场外/货币"""
        if category == "money":
            rank = money_rank
            fields = (
                "income_per_10k",
                "annualized_7d_pct",
                "annualized_14d_pct",
                "annualized_28d_pct",
                "return_1m_pct",
                "return_3m_pct",
                "return_6m_pct",
                "return_1y_pct",
                "return_2y_pct",
                "return_3y_pct",
                "return_5y_pct",
                "return_ytd_pct",
                "return_since_inception_pct",
            )
        elif category == "exchange":
            rank = exchange_rank
            fields = (
                "unit_nav",
                "accumulated_nav",
                "return_1w_pct",
                "return_1m_pct",
                "return_3m_pct",
                "return_6m_pct",
                "return_1y_pct",
                "return_2y_pct",
                "return_3y_pct",
                "return_ytd_pct",
                "return_since_inception_pct",
            )
        else:
            rank = open_rank
            fields = (
                "unit_nav",
                "accumulated_nav",
                "daily_growth_pct",
                "return_1w_pct",
                "return_1m_pct",
                "return_3m_pct",
                "return_6m_pct",
                "return_1y_pct",
                "return_2y_pct",
                "return_3y_pct",
                "return_ytd_pct",
                "return_since_inception_pct",
            )
        if rank is None:
            return None
        return {
            "data_date": rank.data_date,
            **{field: getattr(rank, field) for field in fields},
        }

    @classmethod
    def _fund_payload(
        cls,
        fund,
        open_rank,
        exchange_rank,
        money_rank,
        is_in_watchlist: bool = False,
    ) -> dict[str, Any]:
        """组装响应结果返回"""
        if fund.is_hb:
            category = "money"
        elif fund.is_exchange:
            category = "exchange"
        else:
            category = "open"
        return {
            "id": fund.id,
            "code": fund.code,
            "name": fund.name,
            "fund_type": fund.type,
            "is_hb": fund.is_hb,
            "is_exchange": fund.is_exchange,

            "latest": cls._latest_payload(open_rank, exchange_rank, money_rank, category),
            "is_in_watchlist": is_in_watchlist,
        }
