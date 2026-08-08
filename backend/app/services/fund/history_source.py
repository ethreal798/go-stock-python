"""基金历史数据源适配。

开放式基金沿用 AKShare 的 ``fund_open_fund_info_em``；货币基金使用其
``fund_money_fund_info_em`` 的同一东方财富接口和字段语义，但在本地按字段名
解析，以兼容东方财富新增字段导致的 AKShare 固定列数解析问题。
"""

from __future__ import annotations

import math
import time
from datetime import date
from typing import Any


class FundHistorySourceError(RuntimeError):
    """基金历史接口返回异常。"""


def fetch_open_nav_frames(symbol: str) -> tuple[Any, Any]:
    """获取开放式基金单位净值和累计净值走势。

    ``fund_open_fund_info_em`` 的净值走势接口会返回成立以来的完整序列，
    日期截取交给 formatter 处理。
    """
    try:
        import akshare as ak
    except ImportError as exc:  # pragma: no cover - 运行环境依赖检查
        raise FundHistorySourceError("缺少 akshare，请先安装后端 requirements.txt") from exc

    return (
        ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势", period="3年"),
        ak.fund_open_fund_info_em(symbol=symbol, indicator="累计净值走势", period="3年"),
    )


def _fetch_lsjz_rows(
    symbol: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[Any, list[dict[str, Any]]]:
    """分页读取东财 lsjz，并返回 pandas 模块与原始记录。

    该实现对应 AKShare ``fund_money_fund_info_em`` 的东方财富接口，保留
    每万份收益、7 日年化收益率、申购状态和赎回状态。AKShare 1.18.82
    对当前 14 列原始响应按 13 列重命名，会触发 ``Length mismatch``，因此
    这里按稳定的原始字段名映射，避免整批同步因版本差异失败。
    """
    try:
        import pandas as pd
        import requests
    except ImportError as exc:  # pragma: no cover - 运行环境依赖检查
        raise FundHistorySourceError("缺少历史数据源依赖 requests/pandas") from exc

    url = "https://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/80.0.3987.149 Safari/537.36"
        ),
        "Referer": f"https://fundf10.eastmoney.com/jjjz_{symbol}.html",
        "Host": "api.fund.eastmoney.com",
    }
    start = start_date.isoformat() if start_date else ""
    end = end_date.isoformat() if end_date else ""
    page_size = 20  # 东方财富接口实际按 20 条分页，传更大值会被忽略或返回异常
    params = {
        "fundCode": symbol,
        "pageIndex": 1,
        "pageSize": page_size,
        "startDate": start,
        "endDate": end,
        "_": round(time.time() * 1000),
    }

    def request_page(page_index: int) -> dict[str, Any]:
        params["pageIndex"] = page_index
        try:
            response = requests.get(url, params=params, headers=headers, timeout=(10, 30))
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise FundHistorySourceError(f"基金 {symbol} 历史接口请求失败") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("Data"), dict):
            raise FundHistorySourceError(f"基金 {symbol} 历史接口返回格式异常")
        return payload

    first_payload = request_page(1)
    first_data = first_payload["Data"]
    total_count = int(first_payload.get("TotalCount") or 0)
    total_pages = math.ceil(total_count / page_size) if total_count else 0
    raw_rows: list[dict[str, Any]] = list(first_data.get("LSJZList") or [])
    for page_index in range(2, total_pages + 1):
        raw_rows.extend(request_page(page_index)["Data"].get("LSJZList") or [])

    return pd, raw_rows


def fetch_money_yield_frame(
    symbol: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Any:
    """获取货币基金收益历史，按稳定的东财原始字段名映射。"""
    pd, raw_rows = _fetch_lsjz_rows(symbol, start_date=start_date, end_date=end_date)

    normalized_rows = [
        {
            "净值日期": raw.get("FSRQ"),
            "每万份收益": raw.get("DWJZ"),
            "7日年化收益率": raw.get("LJJZ"),
            "申购状态": raw.get("SGZT"),
            "赎回状态": raw.get("SHZT"),
        }
        for raw in raw_rows
    ]
    return pd.DataFrame(
        normalized_rows,
        columns=["净值日期", "每万份收益", "7日年化收益率", "申购状态", "赎回状态"],
    )


def fetch_exchange_nav_frame(
    symbol: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Any:
    """获取场内 ETF 历史净值，并按东财原始字段名映射。"""
    pd, raw_rows = _fetch_lsjz_rows(symbol, start_date=start_date, end_date=end_date)
    normalized_rows = [
        {
            "净值日期": raw.get("FSRQ"),
            "单位净值": raw.get("DWJZ"),
            "累计净值": raw.get("LJJZ"),
            "日增长率": raw.get("JZZZL"),
            "申购状态": raw.get("SGZT"),
            "赎回状态": raw.get("SHZT"),
        }
        for raw in raw_rows
    ]
    return pd.DataFrame(
        normalized_rows,
        columns=["净值日期", "单位净值", "累计净值", "日增长率", "申购状态", "赎回状态"],
    )
