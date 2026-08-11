"""东方财富基金排行数据源。"""

from __future__ import annotations

import asyncio
from typing import Any


async def fetch_rank_frames() -> tuple[Any, Any, Any]:
    """依次调用三个同步 AKShare 接口，规避其排行解析过程的并发不安全。"""
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("缺少 akshare，请先执行 pip install -r requirements.txt") from exc

    return (
        await asyncio.to_thread(ak.fund_open_fund_rank_em, symbol="全部"),
        await asyncio.to_thread(ak.fund_exchange_rank_em),
        await asyncio.to_thread(ak.fund_money_rank_em),
    )
