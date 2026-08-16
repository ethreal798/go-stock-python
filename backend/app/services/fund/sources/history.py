"""基金历史数据外部来源适配。

开放式基金、场内基金和货币基金统一使用东方财富 ``lsjz`` 接口。
开放式/场内基金仅抓取近 1 年，货币基金抓取近 3 年，再由 formatter
按调用侧传入的日期范围继续截取。
"""

from __future__ import annotations

import math
import time
from datetime import date
from typing import Any


class FundHistorySourceError(RuntimeError):
    """基金历史接口返回异常。"""


def _validate_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("ErrCode") != 0:
        raise FundHistorySourceError(
            f"东方财富接口错误: ErrCode={payload.get('ErrCode')}, " f"ErrMsg={payload.get('ErrMsg')!r}"
        )
    data = payload.get("Data")
    if not isinstance(data, dict) or not isinstance(data.get("LSJZList"), list):
        raise FundHistorySourceError(f"接口响应结构异常: {payload!r}")
    return data["LSJZList"]


def _fetch_lsjz_rows(
    symbol: str,
    *,
    start_date: date,
    end_date: date,
    timeout: tuple[float, float] = (5.0, 15.0),
) -> list[dict[str, Any]]:
    """分页读取东财 lsjz，并仅保留入库所需原始字段。"""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - 运行环境依赖检查
        raise FundHistorySourceError("缺少历史数据源依赖 requests") from exc

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
    params = {
        "fundCode": symbol,
        "pageIndex": 1,
        "pageSize": 20,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "_": round(time.time() * 1000),
    }

    all_rows: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.headers.update(headers)
        total_pages: int | None = None
        page = 1
        while total_pages is None or page <= total_pages:
            params["pageIndex"] = page
            try:
                response = session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise FundHistorySourceError(f"基金 {symbol} 历史接口请求失败") from exc

            rows = _validate_payload(payload)
            if total_pages is None:
                total_count = int(payload.get("TotalCount") or 0)
                server_page_size = int(payload.get("PageSize") or 0)
                if server_page_size <= 0:
                    raise FundHistorySourceError(f"接口返回非法 PageSize: {server_page_size}")
                total_pages = math.ceil(total_count / server_page_size)

            all_rows.extend(
                {
                    "FSRQ": raw.get("FSRQ"),
                    "DWJZ": raw.get("DWJZ"),
                    "LJJZ": raw.get("LJJZ"),
                    "JZZZL": raw.get("JZZZL"),
                }
                for raw in rows
            )
            page += 1

    return all_rows


def _resolve_window(
    *,
    years: int,
) -> tuple[date, date]:
    """根据基金类型收敛抓取窗口。"""

    def _subtract_years(value: date, year: int) -> date:
        """返回按自然年回退后的日期，兼容 2 月 29 日。"""
        try:
            return value.replace(year=value.year - year)
        except ValueError:
            return value.replace(year=value.year - year, month=2, day=28)

    # 1. 如果未传入结束日期则默认为当天日期
    resolved_end = date.today()
    # 2. 根据当天日期反推指定起始日期
    resolved_start = _subtract_years(resolved_end, years)

    return resolved_start, resolved_end


def fetch_open_or_exchange_nav_frames(
    symbol: str,
) -> list[dict[str, Any]]:
    """获取开放式/场内基金近 1 年单位净值和累计净值走势。"""
    resolved_start, resolved_end = _resolve_window(
        years=1,
    )
    raw_rows = _fetch_lsjz_rows(symbol, start_date=resolved_start, end_date=resolved_end)

    return [
        {
            "data_date": raw.get("FSRQ"),
            "unit_nav": raw.get("DWJZ"),
            "accumulated_nav": raw.get("LJJZ"),
            "daily_growth_pct": raw.get("JZZZL"),
        }
        for raw in raw_rows
    ]


def fetch_money_yield_frame(
    symbol: str,
) -> list[dict[str, Any]]:
    """获取货币基金近 3 年收益历史。"""
    resolved_start, resolved_end = _resolve_window(
        years=3,
    )
    raw_rows = _fetch_lsjz_rows(symbol, start_date=resolved_start, end_date=resolved_end)

    return [
        {
            "data_date": raw.get("FSRQ"),
            "income_per_10k": raw.get("DWJZ"),
            "annualized_7d_pct": raw.get("LJJZ"),
        }
        for raw in raw_rows
    ]
