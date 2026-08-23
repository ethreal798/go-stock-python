"""基金排行查询服务。"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import (
    Fund,
    FundExchangeRankLatest,
    FundMoneyRankLatest,
    FundOpenRankLatest,
    FundWatchlistItem,
)
from app.services.fund.common.constants import (
    PERIOD_FIELD_MAP,
    PERIOD_FIELDS,
    SORT_FIELD_MAP,
)


class FundRankingQueryService:
    """基金排行查询服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ================================================================
    # 参数解析
    # ================================================================

    @staticmethod
    def resolve_period(sort: str, period: Optional[str]) -> str:
        """推导 period 的默认值。

        - 若 period 已指定，直接返回。
        - 若 sort 是周期字段（1w~since_inception），period 默认 = sort。
        - 否则默认 "1y"。
        """
        # 周期字段的默认回退值
        _DEFAULT_PERIOD = "1y"

        if period and period != "":
            return period
        if sort in PERIOD_FIELDS:
            return sort
        return _DEFAULT_PERIOD

    @staticmethod
    def get_sort_meta(category: str, sort: str) -> tuple[str, str]:
        """获取排序字段的 (db_column, label)。"""
        valid = SORT_FIELD_MAP.get(category, {})
        if sort not in valid:
            raise ValueError(
                f"分类 '{category}' 不支持排序字段 '{sort}'，"
            )
        return valid[sort]

    @staticmethod
    def get_period_meta(category: str, period: str) -> tuple[str, str]:
        """获取周期字段的 (db_column, label)。"""
        valid = PERIOD_FIELD_MAP.get(category, {})
        if period not in valid:
            raise ValueError(
                f"分类 '{category}' 不支持周期 '{period}'，"
            )
        return valid[period]

    # ================================================================
    # 主查询
    # ================================================================

    async def get_rankings(
        self,
        category: str,
        sort: str,
        period: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        limit: int = 20,
        fund_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取基金排行列表。

        Args:
            category: 基金分类 open/money/exchange
            sort: 排序字段
            period: 显示周期，为 None 时由 sort 推导
            order: asc 或 desc
            page: 页码
            limit: 每页数量
            fund_type: 可选，基金类型过滤
            user_id: 可选，用于标记自选状态

        Returns:
            分页响应 dict
        """
        # 1. 获取周期
        period = self.resolve_period(sort, period)
        # 2. 根据基金类型获取对应 排序列，中文标签
        sort_col, sort_label = self.get_sort_meta(category, sort)
        # 3. 根据记录类型获取对应 周期列，中文标签
        period_col, period_label = self.get_period_meta(category, period)
        # 4. 根据基金类型获取对应排行表
        rank_table = self._get_rank_table(category)
        # 5.
        rank_sort_col = getattr(rank_table, sort_col)

        direction = rank_sort_col.desc() if order == "desc" else rank_sort_col.asc()

        # 基础查询：INNER JOIN（排序字段 IS NOT NULL 已保证有排行数据）
        base_query = select(Fund, rank_table).join(
            rank_table, rank_table.fund_id == Fund.id
        )

        # WHERE: 排序字段 IS NOT NULL
        conditions = [rank_sort_col.is_not(None)]

        # 基金类型过滤
        if fund_type:
            conditions.append(Fund.type == fund_type)

        # 分类过滤（确保 funds 表中的分类标记一致）
        if category == "money":
            conditions.append(Fund.is_hb.is_(True))
        elif category == "exchange":
            conditions.append(Fund.is_exchange.is_(True))
        else:
            conditions.append(
                and_(Fund.is_hb.is_(False), Fund.is_exchange.is_(False))
            )

        if len(conditions) > 1:
            base_query = base_query.where(and_(*conditions))
        else:
            base_query = base_query.where(conditions[0])

        # 1. 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # 2. 分页查询
        offset_val = (page - 1) * limit
        page_query = (
            base_query.order_by(direction, Fund.code)
            .offset(offset_val)
            .limit(limit)
        )
        rows = list((await self.db.execute(page_query)).all())

        # 3. 查询自选集合
        watchlist_codes = await self._watchlist_codes(user_id)

        # 4. 组装响应
        items = []
        for fund, rank in rows:
            latest = self._build_latest(rank, category)
            item: dict[str, Any] = {
                "code": fund.code,
                "name": fund.name,
                "type": fund.type,
                "category": category,
                "data_date": rank.data_date,
                "latest": latest,
                "is_in_watchlist": fund.code in watchlist_codes,
            }
            items.append(item)

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "category": category,
            "sort": sort,
            "period": period,
            "order": order,
        }

    # ================================================================
    # 辅助方法
    # ================================================================

    @staticmethod
    def _get_rank_table(category: str):
        """根据分类获取对应的排行表模型。"""
        tables = {
            "open": FundOpenRankLatest,
            "exchange": FundExchangeRankLatest,
            "money": FundMoneyRankLatest,
        }
        if category not in tables:
            raise ValueError(f"未知分类: {category}")
        return tables[category]

    @staticmethod
    def _build_latest(rank, category: str) -> dict[str, Any]:
        """根据分类构建 FundLatestResponse 结构。"""
        if category == "money":
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
                "return_5y_pct",
                "return_ytd_pct",
                "return_since_inception_pct",
            )
        result: dict[str, Any] = {}
        for field in fields:
            result[field] = getattr(rank, field, None)
        return result

    async def _watchlist_codes(self, user_id: Optional[int]) -> set[str]:
        """查询当前用户的基金自选代码。"""
        if user_id is None:
            return set()
        statement = select(FundWatchlistItem.fund_code).where(
            FundWatchlistItem.user_id == user_id
        )
        return set((await self.db.execute(statement)).scalars().all())
