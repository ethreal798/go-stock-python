"""基金累计收益率走势同步命令行入口。

示例：
    python -m app.services.fund.sync_performance_trends --followed
    python -m app.services.fund.sync_performance_trends --fund-code 007339 --period 1y
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.core.redis import close_redis
from app.services.fund.performance_trend_source import PERIOD_TO_SOURCE_TYPE
from app.services.fund.performance_trend_sync import FundPerformanceTrendSyncService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步开放式基金累计收益率走势最新快照")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--followed", action="store_true", help="同步所有被关注的开放式基金")
    target.add_argument("--fund-code", action="append", dest="fund_codes", help="同步指定基金，可重复传入")
    parser.add_argument(
        "--period",
        action="append",
        choices=tuple(PERIOD_TO_SOURCE_TYPE),
        dest="periods",
        help="同步周期，可重复传入；默认1y",
    )
    parser.add_argument("--concurrency", type=int, help="数据源并发数")
    parser.add_argument("--batch-size", type=int, help="每批快照任务数")
    parser.add_argument("--retries", type=int, help="失败重试次数")
    parser.add_argument("--timeout", type=float, help="单次请求超时秒数")
    return parser


async def _run(args: argparse.Namespace) -> None:
    periods = args.periods or ["1y"]
    kwargs = {
        key: value
        for key, value in {
            "periods": periods,
            "concurrency": args.concurrency,
            "batch_size": args.batch_size,
            "retries": args.retries,
            "timeout": args.timeout,
        }.items()
        if value is not None
    }
    async with async_session_factory() as db:
        service = FundPerformanceTrendSyncService(db)
        try:
            if args.followed:
                result = await service.fetch_and_sync_followed(**kwargs)
            else:
                result = await service.fetch_and_sync_codes(args.fund_codes, **kwargs)
            logging.getLogger(__name__).info("基金累计收益率走势同步结果: %s", result)
        except Exception:
            await db.rollback()
            logging.getLogger(__name__).exception("基金累计收益率走势同步失败")
            raise
    await close_redis()
    await close_db()


def main() -> None:
    setup_logging()
    asyncio.run(_run(_build_parser().parse_args()))


if __name__ == "__main__":
    main()
