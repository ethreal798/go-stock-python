"""东方财富开放式基金累计收益率走势数据源。"""

from __future__ import annotations

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
