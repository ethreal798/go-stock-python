from __future__ import annotations

from typing import Any

import requests

from bs4 import BeautifulSoup

"""根据akshare 基金净值下的 三个基金类型净值接口 获取可用基金代码 结合基金基本信息接口
推导出 可用基金 对应 基金类型 is_hb is_exchange
"""


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
    """获取全量基金目录（代码、名称、类型）。"""
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


def fetch_open_fund_codes() -> set[str]:
    """获取开放式基金代码集合。"""
    try:
        url = "https://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
        params = {
            "t": "1",
            "lx": "1",
            "letter": "",
            "gsid": "",
            "text": "",
            "sort": "zdf,desc",
            "page": "1,50000",
            "dt": "1580914040623",
            "atfc": "",
            "onlySale": "0",
        }
        response = requests.get(url, params=params, headers=_HEADERS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FundCatalogSourceError("开放式基金接口请求失败") from exc

    try:
        from py_mini_racer import MiniRacer

        ctx = MiniRacer()
        ctx.eval(response.text)
        fund_datas = ctx.execute("db").get("datas")
    except Exception as exc:
        raise FundCatalogSourceError("开放式基金 JS 解析失败") from exc

    return {fund[0] for fund in fund_datas if isinstance(fund, (list, tuple)) and len(fund) > 0}


def fetch_money_fund_codes() -> set[str]:
    """获取货币基金代码集合。"""
    try:
        url = "https://fund.eastmoney.com/HBJJ_pjsyl.html"
        response = requests.get(url, headers=_HEADERS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FundCatalogSourceError("货币基金接口请求失败") from exc

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        codes: set[str] = set()
        for row in soup.select('tr[id^="tr"]'):
            cells = row.find_all("td")
            if len(cells) >= 4:
                code = cells[3].get_text(strip=True)
                if code:
                    codes.add(code)
        return codes
    except Exception as exc:
        raise FundCatalogSourceError("货币基金 HTML 解析失败") from exc


def fetch_exchange_fund_codes() -> set[str]:
    """获取场内基金代码集合。"""
    try:
        url = "https://fund.eastmoney.com/cnjy_dwjz.html"
        response = requests.get(url, headers=_HEADERS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FundCatalogSourceError("场内基金接口请求失败") from exc

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 2:
            return set()
        target_table = tables[1]
        codes: set[str] = set()
        for row in target_table.find_all("tr")[2:]:
            cells = row.find_all("td")
            if len(cells) >= 4:
                code = cells[3].get_text(strip=True)
                if code:
                    codes.add(code)
        return codes
    except Exception as exc:
        raise FundCatalogSourceError("场内基金 HTML 解析失败") from exc
