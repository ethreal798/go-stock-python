"""东方财富基金排行数据源。"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any


class FundRankingSourceError(RuntimeError):
    """基金排行接口返回异常。"""


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/81.0.4044.138 Safari/537.36"
    ),
    "Referer": "https://fund.eastmoney.com/fundguzhi.html",
}


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _field(fields: list[str], index: int) -> str | None:
    try:
        return fields[index]
    except IndexError:
        return None


def _decode_assignment_payload(text: str) -> dict[str, Any]:
    """解析 rankhandler 返回的 JavaScript 赋值对象。"""
    payload = text.strip()
    if not payload:
        raise FundRankingSourceError("开放/场内基金排行接口返回空响应")
    if "=" in payload:
        payload = payload.split("=", 1)[1].strip()
    payload = payload.rstrip(";")
    payload = re.sub(r"([{,])\s*([a-zA-Z_]\w*)\s*:", r'\1"\2":', payload)
    payload = re.sub(r",\s*([}\]])", r"\1", payload)
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise FundRankingSourceError("开放/场内基金排行接口 JSON 解析失败") from exc
    if not isinstance(decoded, dict):
        raise FundRankingSourceError("开放/场内基金排行接口响应结构异常")
    return decoded


def _parse_open_or_exchange_row(raw: str, category: str) -> dict[str, Any]:
    fields = raw.split(",")
    if category == "open":
        return {
            "fund_code": _field(fields, 0),
            "fund_name": _field(fields, 1),
            "data_date": _field(fields, 3),
            "unit_nav": _to_float(_field(fields, 4)),
            "accumulated_nav": _to_float(_field(fields, 5)),
            "daily_growth_pct": _to_float(_field(fields, 6)),
            "return_1w_pct": _to_float(_field(fields, 7)),
            "return_1m_pct": _to_float(_field(fields, 8)),
            "return_3m_pct": _to_float(_field(fields, 9)),
            "return_6m_pct": _to_float(_field(fields, 10)),
            "return_1y_pct": _to_float(_field(fields, 11)),
            "return_2y_pct": _to_float(_field(fields, 12)),
            "return_3y_pct": _to_float(_field(fields, 13)),
            "return_5y_pct": _to_float(_field(fields, 24)),
            "return_ytd_pct": _to_float(_field(fields, 14)),
            "return_since_inception_pct": _to_float(_field(fields, 15)),
        }
    return {
        "fund_code": _field(fields, 0),
        "fund_name": _field(fields, 1),
        "fund_type": _field(fields, -2),
        "data_date": _field(fields, 3),
        "unit_nav": _to_float(_field(fields, 4)),
        "accumulated_nav": _to_float(_field(fields, 5)),
        "return_1w_pct": _to_float(_field(fields, 6)),
        "return_1m_pct": _to_float(_field(fields, 7)),
        "return_3m_pct": _to_float(_field(fields, 8)),
        "return_6m_pct": _to_float(_field(fields, 9)),
        "return_1y_pct": _to_float(_field(fields, 10)),
        "return_2y_pct": _to_float(_field(fields, 11)),
        "return_3y_pct": _to_float(_field(fields, 12)),
        "return_ytd_pct": _to_float(_field(fields, 13)),
        "return_since_inception_pct": _to_float(_field(fields, 14)),
        # "inception_date": _field(fields, 15),
    }


def fetch_open_or_exchange_rank_rows(category: str) -> list[dict[str, Any]]:
    """获取开放式或场内基金排行，并返回标准字段记录。"""
    if category not in {"open", "exchange"}:
        raise ValueError(f"不支持的基金排行分类: {category}")
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - 运行环境依赖检查
        raise FundRankingSourceError("缺少数据源依赖 requests") from exc

    params = {
        "op": "ph",
        "dt": "fb",
        "ft": "all",
        "gs": "0",
        "sc": "1nzf",
        "st": "desc",
        "pi": "1",
        "pn": "30000",
        "v": "0.1591891419018292",
    }
    if category == "open":
        params.update({"dx": "1", "dt": "kf"})
    try:
        response = requests.get(
            "https://fund.eastmoney.com/data/rankhandler.aspx",
            params=params,
            headers=_HEADERS,
            timeout=(5, 30),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FundRankingSourceError(f"{category} 基金排行接口请求失败") from exc

    payload = _decode_assignment_payload(response.text)
    raw_rows = payload.get("datas")
    if not isinstance(raw_rows, list):
        raise FundRankingSourceError(f"{category} 基金排行接口响应结构异常")
    return [_parse_open_or_exchange_row(row, category) for row in raw_rows if isinstance(row, str)]


def _parse_money_row(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "fund_code": raw.get("FCODE"),
        "fund_name": raw.get("SHORTNAME"),
        "data_date": raw.get("FSRQ"),
        "income_per_10k": _to_float(raw.get("DWJZ")),
        "annualized_7d_pct": _to_float(raw.get("LJJZ")),
        "annualized_14d_pct": _to_float(raw.get("FTYI")),
        "annualized_28d_pct": _to_float(raw.get("TEYI")),
        "return_1m_pct": _to_float(raw.get("SYL_Y")),
        "return_3m_pct": _to_float(raw.get("SYL_3Y")),
        "return_6m_pct": _to_float(raw.get("SYL_6Y")),
        "return_1y_pct": _to_float(raw.get("SYL_1N")),
        "return_2y_pct": _to_float(raw.get("SYL_2N")),
        "return_3y_pct": _to_float(raw.get("SYL_3N")),
        "return_5y_pct": _to_float(raw.get("SYL_5N")),
        "return_ytd_pct": _to_float(raw.get("SYL_JN")),
        "return_since_inception_pct": _to_float(raw.get("SYL_LN")),
    }


def fetch_money_rank_rows() -> list[dict[str, Any]]:
    """获取货币基金排行，并返回标准字段记录。"""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - 运行环境依赖检查
        raise FundRankingSourceError("缺少数据源依赖 requests") from exc

    try:
        response = requests.get(
            "https://api.fund.eastmoney.com/FundRank/GetHbRankList",
            params={
                "intCompany": "0",
                "MinsgType": "",
                "IsSale": "1",
                "strSortCol": "LJJZ",
                "orderType": "desc",
                "pageIndex": "1",
                "pageSize": "10000",
            },
            headers=_HEADERS,
            timeout=(5, 30),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise FundRankingSourceError("货币基金排行接口请求失败") from exc

    raw_rows = payload.get("Data") if isinstance(payload, dict) else None
    if not isinstance(raw_rows, list):
        raise FundRankingSourceError("货币基金排行接口响应结构异常")
    return [_parse_money_row(row) for row in raw_rows if isinstance(row, dict)]


async def fetch_rank_frames() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """并行抓取开放式、场内和货币基金排行记录。"""
    open_rows, exchange_rows, money_rows = await asyncio.gather(
        asyncio.to_thread(fetch_open_or_exchange_rank_rows, "open"),
        asyncio.to_thread(fetch_open_or_exchange_rank_rows, "exchange"),
        asyncio.to_thread(fetch_money_rank_rows),
    )
    return open_rows, exchange_rows, money_rows
