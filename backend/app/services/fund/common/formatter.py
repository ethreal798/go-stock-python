"""基金数据到标准入库记录的格式化方法。"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from app.services.fund.common.constants import FundMetadataColumns
from app.services.fund.common.utils import (
    dataframe_records,
    normalize_date,
    normalize_decimal,
    normalize_fund_code,
    normalize_text,
)

# ------------------------------------------------------------------
# 基金累计收益率走势
# ------------------------------------------------------------------
MAX_PERFORMANCE_TREND_POINTS_PER_SERIES = 2000
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def _performance_trend_series_identity(index: int) -> tuple[str, str | None]:
    if index == 0:
        return "fund", None
    if index == 1:
        return "peer_average", None
    if index == 2:
        return "index:000300", "000300"
    return f"source_series:{index}", None


def _normalize_performance_trend_point(raw: Any) -> tuple[str, float]:
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        raise ValueError(f"无效走势点: {raw!r}")
    try:
        timestamp_ms = Decimal(str(raw[0]))
        value = Decimal(str(raw[1]))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"无法转换走势点: {raw!r}") from exc
    if not timestamp_ms.is_finite() or not value.is_finite():
        raise ValueError(f"走势点包含非有限数值: {raw!r}")
    point_date = datetime.fromtimestamp(float(timestamp_ms) / 1000, tz=timezone.utc).astimezone(SHANGHAI_TZ).date()
    return point_date.isoformat(), float(value)


def format_performance_trend_snapshot(
    payload: dict[str, Any],
    *,
    fund_code: str,
    period: str,
    fetched_at: datetime,
    fresh_seconds: int,
) -> dict[str, Any]:
    """把东方财富响应格式化为可直接供 ECharts 使用的最新快照。"""
    if fresh_seconds < 1:
        raise ValueError("fresh_seconds 必须大于 0")

    series: list[dict[str, Any]] = []
    all_dates: list[str] = []
    for index, raw_series in enumerate(payload.get("Data") or []):
        if not isinstance(raw_series, dict):
            raise ValueError(f"基金 {fund_code} 第 {index} 条曲线格式异常")
        name = str(raw_series.get("name") or "").strip() or f"曲线{index + 1}"
        raw_points = raw_series.get("data")
        if not isinstance(raw_points, list) or not raw_points:
            raise ValueError(f"基金 {fund_code} 曲线 {name} 没有有效数据")
        if len(raw_points) > MAX_PERFORMANCE_TREND_POINTS_PER_SERIES:
            raise ValueError(f"基金 {fund_code} 曲线 {name} 点数超过限制: {len(raw_points)}")

        # 上游偶尔可能重复返回同一天，保留最后一个点并按日期升序。
        deduplicated = dict(_normalize_performance_trend_point(point) for point in raw_points)
        points = [[point_date, value] for point_date, value in sorted(deduplicated.items())]
        if not points:
            raise ValueError(f"基金 {fund_code} 曲线 {name} 清洗后为空")
        key, benchmark_code = _performance_trend_series_identity(index)
        series.append(
            {
                "key": key,
                "name": name,
                "benchmark_code": benchmark_code,
                "latest_return_pct": points[-1][1],
                "points": points,
            }
        )
        all_dates.extend(point[0] for point in points)

    if not series or series[0]["key"] != "fund":
        raise ValueError(f"基金 {fund_code} 缺少本基金收益率曲线")

    canonical = json.dumps(series, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return {
        "period": period,
        "start_date": date.fromisoformat(min(all_dates)),
        "end_date": date.fromisoformat(max(all_dates)),
        "series_data": series,
        "source": "eastmoney",
        "schema_version": 1,
        "content_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "point_count": sum(len(item["points"]) for item in series),
        "fetched_at": fetched_at,
        "expires_at": fetched_at + timedelta(seconds=fresh_seconds),
    }


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
