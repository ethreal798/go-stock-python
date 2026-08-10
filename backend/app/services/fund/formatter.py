"""AKShare 基金 DataFrame 到标准入库记录的格式化方法。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.fund.constants import FundHistoryColumns, FundMetadataColumns, FundRankingColumns
from app.services.fund.utils import (
    dataframe_records,
    ensure_unique_fund_codes,
    normalize_date,
    normalize_decimal,
    normalize_fund_code,
    normalize_text,
)


# ------------------------------------------------------------------
# 基金排行
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# 净值
# ------------------------------------------------------------------
def _history_records(
    frame: Any,
    required_columns: set[str] | frozenset[str],
    source: str,
) -> list[dict[str, Any]]:
    """读取单只基金历史 DataFrame；数据源为空时返回空列表。"""
    columns = getattr(frame, "columns", None) if frame is not None else None
    if columns is None or len(columns) == 0:
        return []
    return dataframe_records(frame, required_columns, source, minimum_rows=0)


def _in_date_range(value: date | None, start_date: date, end_date: date) -> bool:
    return value is not None and start_date <= value <= end_date


def format_open_nav_history(
    unit_nav_frame: Any,
    accumulated_nav_frame: Any,
    *,
    start_date: date,
    end_date: date,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    """合并开放式基金单位净值和累计净值走势，并截取指定日期范围。"""
    unit_by_date: dict[date, dict[str, Any]] = {}
    for raw in _history_records(
        unit_nav_frame,
        FundHistoryColumns.OPEN_UNIT_NAV,
        "开放式基金单位净值历史",
    ):
        data_date = normalize_date(raw["净值日期"])
        if not _in_date_range(data_date, start_date, end_date):
            continue
        unit_by_date[data_date] = {
            "unit_nav": normalize_decimal(raw["单位净值"]),
            "daily_growth_pct": normalize_decimal(raw["日增长率"]),
        }

    accumulated_by_date: dict[date, Any] = {}
    for raw in _history_records(
        accumulated_nav_frame,
        FundHistoryColumns.OPEN_ACCUMULATED_NAV,
        "开放式基金累计净值历史",
    ):
        data_date = normalize_date(raw["净值日期"])
        if _in_date_range(data_date, start_date, end_date):
            accumulated_by_date[data_date] = normalize_decimal(raw["累计净值"])

    rows = []
    for data_date in sorted(set(unit_by_date) | set(accumulated_by_date)):
        unit = unit_by_date.get(data_date, {})
        accumulated_nav = accumulated_by_date.get(data_date)
        if unit.get("unit_nav") is None and accumulated_nav is None:
            continue
        rows.append(
            {
                "data_date": data_date,
                "unit_nav": unit.get("unit_nav"),
                "accumulated_nav": accumulated_nav,
                "daily_growth_pct": unit.get("daily_growth_pct"),
                "fetched_at": fetched_at,
            }
        )
    return rows


def format_money_yield_history(
    frame: Any,
    *,
    start_date: date,
    end_date: date,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    """格式化货币基金每万份收益和七日年化收益率历史。"""
    rows = []
    for raw in _history_records(frame, FundHistoryColumns.MONEY_YIELD, "货币基金收益历史"):
        data_date = normalize_date(raw["净值日期"])
        if not _in_date_range(data_date, start_date, end_date):
            continue
        income_per_10k = normalize_decimal(raw["每万份收益"])
        annualized_7d_pct = normalize_decimal(raw["7日年化收益率"])
        if income_per_10k is None and annualized_7d_pct is None:
            continue
        rows.append(
            {
                "data_date": data_date,
                "income_per_10k": income_per_10k,
                "annualized_7d_pct": annualized_7d_pct,
                "purchase_status": normalize_text(raw.get("申购状态")),
                "redemption_status": normalize_text(raw.get("赎回状态")),
                "fetched_at": fetched_at,
            }
        )
    rows.sort(key=lambda row: row["data_date"])
    return rows


def format_exchange_nav_history(
    frame: Any,
    *,
    start_date: date,
    end_date: date,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    """格式化场内 ETF 净值历史；保留申购和赎回状态。"""
    rows = []
    for raw in _history_records(frame, FundHistoryColumns.EXCHANGE_NAV, "场内 ETF 净值历史"):
        data_date = normalize_date(raw["净值日期"])
        if not _in_date_range(data_date, start_date, end_date):
            continue
        unit_nav = normalize_decimal(raw["单位净值"])
        accumulated_nav = normalize_decimal(raw["累计净值"])
        if unit_nav is None and accumulated_nav is None:
            continue
        rows.append(
            {
                "data_date": data_date,
                "unit_nav": unit_nav,
                "accumulated_nav": accumulated_nav,
                "daily_growth_pct": normalize_decimal(raw["日增长率"]),
                "purchase_status": normalize_text(raw.get("申购状态")),
                "redemption_status": normalize_text(raw.get("赎回状态")),
                "fetched_at": fetched_at,
            }
        )
    rows.sort(key=lambda row: row["data_date"])
    return rows


# ------------------------------------------------------------------
# 基金档案与风险指标
# ------------------------------------------------------------------
def _normalize_scale_cny(value: Any) -> Decimal | None:
    """将雪球的基金规模转换为人民币元。"""
    text = normalize_text(value)
    if text is None:
        return None
    multipliers = {
        "万亿": Decimal("1000000000000"),
        "亿": Decimal("100000000"),
        "万": Decimal("10000"),
        "元": Decimal("1"),
    }
    for suffix, multiplier in multipliers.items():
        if text.endswith(suffix):
            number = normalize_decimal(text.removesuffix(suffix))
            return number * multiplier if number is not None else None
    return normalize_decimal(text)


def format_fund_profile(
    frame: Any,
    *,
    fund_code: str,
    fetched_at: datetime,
) -> dict[str, Any]:
    """将雪球 item/value 基金基本信息转换为档案最新记录。"""
    records = dataframe_records(frame, FundMetadataColumns.PROFILE, "雪球基金基本信息", minimum_rows=1)
    items = {normalize_text(row["item"]): row.get("value") for row in records if normalize_text(row["item"])}
    source_code = normalize_text(items.get("基金代码"))
    if source_code is not None and normalize_fund_code(source_code) != fund_code:
        raise ValueError(f"雪球基金基本信息代码不匹配: requested={fund_code}, returned={source_code}")
    fund_name = normalize_text(items.get("基金名称"))
    if fund_name is None:
        raise ValueError(f"雪球基金基本信息缺少基金名称: {fund_code}")
    return {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "full_name": normalize_text(items.get("基金全称")),
        "inception_date": normalize_date(items.get("成立时间")),
        "latest_scale_cny": _normalize_scale_cny(items.get("最新规模")),
        "fund_company": normalize_text(items.get("基金公司")),
        "fund_manager": normalize_text(items.get("基金经理")),
        "custodian_bank": normalize_text(items.get("托管银行")),
        "fund_type": normalize_text(items.get("基金类型")),
        "rating_agency": normalize_text(items.get("评级机构")),
        "fund_rating": normalize_text(items.get("基金评级")),
        "investment_strategy": normalize_text(items.get("投资策略")),
        "investment_objective": normalize_text(items.get("投资目标")),
        "performance_benchmark": normalize_text(items.get("业绩比较基准")),
        "fetched_at": fetched_at,
    }


def format_fund_risk_metrics(
    frame: Any,
    *,
    fund_code: str,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    """格式化雪球按周期返回的基金风险指标。"""
    columns = getattr(frame, "columns", None) if frame is not None else None
    if columns is None or len(columns) == 0:
        return []
    rows = []
    seen_periods: set[str] = set()
    for raw in dataframe_records(frame, FundMetadataColumns.RISK, "雪球基金风险指标", minimum_rows=0):
        period = normalize_text(raw["周期"])
        if period is None:
            continue
        if period in seen_periods:
            raise ValueError(f"雪球基金风险指标返回重复周期: fund={fund_code}, period={period}")
        seen_periods.add(period)
        metrics = {
            "peer_risk_return_score": normalize_decimal(raw["较同类风险收益比"]),
            "peer_risk_control_score": normalize_decimal(raw["较同类抗风险波动"]),
            "annualized_volatility_pct": normalize_decimal(raw["年化波动率"]),
            "annualized_sharpe_ratio": normalize_decimal(raw["年化夏普比率"]),
            "max_drawdown_pct": normalize_decimal(raw["最大回撤"]),
        }
        if all(value is None for value in metrics.values()):
            continue
        rows.append(
            {
                "fund_code": fund_code,
                "period": period,
                **metrics,
                "fetched_at": fetched_at,
            }
        )
    return rows
