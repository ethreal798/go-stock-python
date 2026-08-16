from __future__ import annotations

from typing import Any

import requests


class FundCatalogSourceError(RuntimeError):
    pass


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
}


def fetch_fund_catalog() -> list[dict[str, Any]]:
    try:
        response = requests.get(
            "https://fund.eastmoney.com/js/fundcode_search.js",
            headers=_HEADERS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FundCatalogSourceError("基金目录接口请求失败") from exc

    try:
        from py_mini_racer import MiniRacer

        ctx = MiniRacer()
        ctx.eval(response.text)
        result = ctx.execute("r")
    except Exception as exc:
        raise FundCatalogSourceError("基金目录 JS 解析失败") from exc

    if not isinstance(result, list) or not result:
        raise FundCatalogSourceError("基金目录接口返回空列表")

    return [
        {
            "code": item[0],
            "name": item[2],
            "type": item[3],
        }
        for item in result
        if isinstance(item, list)
    ]
