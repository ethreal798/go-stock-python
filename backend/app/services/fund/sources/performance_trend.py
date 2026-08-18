"""东方财富开放式基金累计收益率走势外部来源。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

PERIOD_TO_SOURCE_TYPE = {
    "1m": "m",
    "3m": "q",
    "6m": "hy",
    "1y": "y",
    "3y": "try",
    "5y": "fiy",
    "ytd": "sy",
    "since_inception": "se",
}

EASTMONEY_TREND_URL = "https://api.fund.eastmoney.com/pinzhong/LJSYLZS"

PERIOD_TO_DATE_RANGE = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "3y": 3 * 365,
    "5y": 5 * 365,
}


def resolve_date_range(period: str) -> tuple[date | None, date]:
    """将周期解析为 (start_date, end_date)。start_date 为 None 表示不限。"""
    end_date = date.today()
    if period == "ytd":
        return date(end_date.year, 1, 1), end_date
    if period == "since_inception":
        return None, end_date
    days = PERIOD_TO_DATE_RANGE.get(period)
    if days is None:
        raise ValueError(f"不支持的周期: {period}")
    return end_date - timedelta(days=days), end_date


class FundPerformanceTrendSourceError(RuntimeError):
    """东方财富累计收益率走势请求或响应异常。"""


async def fetch_performance_trend_payload(
    symbol: str,
    period: str,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """一次读取本基金、同类平均和沪深300三条曲线的原始响应。"""
    source_type = PERIOD_TO_SOURCE_TYPE.get(period)
    if source_type is None:
        raise ValueError(f"不支持的基金走势周期: {period}")

    try:
        response = await client.get(
            EASTMONEY_TREND_URL,
            params={"fundCode": symbol, "indexcode": "000300", "type": source_type},
            headers={"Referer": "https://fund.eastmoney.com/", "User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FundPerformanceTrendSourceError(f"基金 {symbol} 累计收益率走势请求失败") from exc

    if not isinstance(payload, dict) or payload.get("ErrCode") != 0 or not isinstance(payload.get("Data"), list):
        raise FundPerformanceTrendSourceError(f"基金 {symbol} 累计收益率走势返回格式异常")
    if not payload["Data"]:
        raise FundPerformanceTrendSourceError(f"基金 {symbol} 累计收益率走势为空")
    return payload
