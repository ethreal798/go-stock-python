"""AKShare 基金 DataFrame 到标准入库记录的格式化方法。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.fund.constants import FundRankingColumns
from app.services.fund.utils import (
    dataframe_records,
    ensure_unique_fund_codes,
    normalize_date,
    normalize_decimal,
    normalize_fund_code,
    normalize_text,
)


def format_open_rank(frame: Any, fetched_at: datetime, minimum_rows: int = 1) -> list[dict[str, Any]]:
    """格式化开放式基金排行；LOF 按东方财富口径包含在内。"""
    rows = []
    for raw in dataframe_records(frame, FundRankingColumns.OPEN, "开放式基金排行", minimum_rows):
        name = normalize_text(raw["基金简称"])
        if name is None:
            raise ValueError(f"开放式基金排行关键字段为空: {raw!r}")
        rows.append(
            {
                "fund_code": normalize_fund_code(raw["基金代码"]),
                "fund_name": name,
                "data_date": normalize_date(raw["日期"]),
                "unit_nav": normalize_decimal(raw["单位净值"]),
                "accumulated_nav": normalize_decimal(raw["累计净值"]),
                "daily_growth_pct": normalize_decimal(raw["日增长率"]),
                "return_1w_pct": normalize_decimal(raw["近1周"]),
                "return_1m_pct": normalize_decimal(raw["近1月"]),
                "return_3m_pct": normalize_decimal(raw["近3月"]),
                "return_6m_pct": normalize_decimal(raw["近6月"]),
                "return_1y_pct": normalize_decimal(raw["近1年"]),
                "return_2y_pct": normalize_decimal(raw["近2年"]),
                "return_3y_pct": normalize_decimal(raw["近3年"]),
                "return_ytd_pct": normalize_decimal(raw["今年来"]),
                "return_since_inception_pct": normalize_decimal(raw["成立来"]),
                "fetched_at": fetched_at,
            }
        )
    return ensure_unique_fund_codes(rows, "开放式基金排行")


def format_exchange_rank(frame: Any, fetched_at: datetime, minimum_rows: int = 1) -> list[dict[str, Any]]:
    """格式化场内交易基金排行。"""
    rows = []
    for raw in dataframe_records(frame, FundRankingColumns.EXCHANGE, "场内交易基金排行", minimum_rows):
        name = normalize_text(raw["基金简称"])
        if name is None:
            raise ValueError(f"场内交易基金排行关键字段为空: {raw!r}")
        rows.append(
            {
                "fund_code": normalize_fund_code(raw["基金代码"]),
                "fund_name": name,
                "fund_type": normalize_text(raw["类型"]),
                "data_date": normalize_date(raw["日期"]),
                "unit_nav": normalize_decimal(raw["单位净值"]),
                "accumulated_nav": normalize_decimal(raw["累计净值"]),
                "return_1w_pct": normalize_decimal(raw["近1周"]),
                "return_1m_pct": normalize_decimal(raw["近1月"]),
                "return_3m_pct": normalize_decimal(raw["近3月"]),
                "return_6m_pct": normalize_decimal(raw["近6月"]),
                "return_1y_pct": normalize_decimal(raw["近1年"]),
                "return_2y_pct": normalize_decimal(raw["近2年"]),
                "return_3y_pct": normalize_decimal(raw["近3年"]),
                "return_ytd_pct": normalize_decimal(raw["今年来"]),
                "return_since_inception_pct": normalize_decimal(raw["成立来"]),
                "inception_date": normalize_date(raw["成立日期"]),
                "fetched_at": fetched_at,
            }
        )
    return ensure_unique_fund_codes(rows, "场内交易基金排行")


def format_money_rank(frame: Any, fetched_at: datetime, minimum_rows: int = 1) -> list[dict[str, Any]]:
    """格式化货币型基金排行。"""
    rows = []
    for raw in dataframe_records(frame, FundRankingColumns.MONEY, "货币型基金排行", minimum_rows):
        name = normalize_text(raw["基金简称"])
        if name is None:
            raise ValueError(f"货币型基金排行关键字段为空: {raw!r}")
        rows.append(
            {
                "fund_code": normalize_fund_code(raw["基金代码"]),
                "fund_name": name,
                "data_date": normalize_date(raw["日期"]),
                # 东方财富文档标注有误：万份收益是元/万份，不是百分比。
                "income_per_10k": normalize_decimal(raw["万份收益"]),
                "annualized_7d_pct": normalize_decimal(raw["年化收益率7日"]),
                "annualized_14d_pct": normalize_decimal(raw["年化收益率14日"]),
                "annualized_28d_pct": normalize_decimal(raw["年化收益率28日"]),
                "return_1m_pct": normalize_decimal(raw["近1月"]),
                "return_3m_pct": normalize_decimal(raw["近3月"]),
                "return_6m_pct": normalize_decimal(raw["近6月"]),
                "return_1y_pct": normalize_decimal(raw["近1年"]),
                "return_2y_pct": normalize_decimal(raw["近2年"]),
                "return_3y_pct": normalize_decimal(raw["近3年"]),
                "return_5y_pct": normalize_decimal(raw["近5年"]),
                "return_ytd_pct": normalize_decimal(raw["今年来"]),
                "return_since_inception_pct": normalize_decimal(raw["成立来"]),
                "fetched_at": fetched_at,
            }
        )
    return ensure_unique_fund_codes(rows, "货币型基金排行")
