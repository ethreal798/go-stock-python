"""基金累计收益率走势同步命令行入口。

按需刷新指定基金的走势快照到 fund_performance_trend_latest 表。
货币基金会走增量同步路径（从 fund_money_yield_history 查询）。

开发环境运行：
    cd backend
    # 同步指定基金的多个周期
    python -m app.commands.fund.sync_performance_trends --fund-code 007339 --period 1y
    python -m app.commands.fund.sync_performance_trends --fund-code 007339 --fund-code 000211 --period 1m --period 3m

Docker 容器中运行：
    # 开发模式（容器已启动，挂载了本地代码）
    docker compose exec backend python -m app.commands.fund.sync_performance_trends --fund-code 007339 --period 1y

    # 生产模式（临时启动一个容器执行后退出）
    docker compose run --rm backend python -m app.commands.fund.sync_performance_trends --fund-code 007339 --period 1y
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.core.redis import close_redis
from app.services.fund.sources.performance_trend import PERIOD_TO_SOURCE_TYPE
from app.services.fund.sync.performance_trend import FundPerformanceTrendSyncService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步开放式基金累计收益率走势最新快照")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--fund-code", action="append", dest="fund_codes", help="同步指定基金，可重复传入")
    parser.add_argument(
        "--period",
        action="append",
        choices=tuple(PERIOD_TO_SOURCE_TYPE),
        dest="periods",
        help="同步周期，可重复传入；默认1y",
    )
    return parser


async def _run(args: argparse.Namespace) -> None:
    periods = args.periods or ["1y"]
    kwargs = {
        key: value
        for key, value in {
            "periods": periods,
        }.items()
        if value is not None
    }
    async with async_session_factory() as db:
        service = FundPerformanceTrendSyncService(db)
        try:
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
