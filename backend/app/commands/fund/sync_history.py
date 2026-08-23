"""基金历史净值/收益同步命令行入口。

同步开放式/场内基金的历史净值，以及货币基金的每日收益历史。
支持全量同步、增量同步和指定基金代码同步。

开发环境运行：
    cd backend
    # 同步全部基金历史
    python -m app.commands.fund.sync_history all
    # 增量同步全部基金（推荐日常使用）
    python -m app.commands.fund.sync_history incremental
    # 同步指定基金代码
    python -m app.commands.fund.sync_history codes 007339 000211

Docker 容器中运行：
    # 开发模式（容器已启动，挂载了本地代码）
    docker compose exec backend python -m app.commands.fund.sync_history all
    docker compose exec backend python -m app.commands.fund.sync_history incremental
    docker compose exec backend python -m app.commands.fund.sync_history codes 007339

    # 生产模式（临时启动一个容器执行后退出）
    docker compose run --rm backend python -m app.commands.fund.sync_history all
    docker compose run --rm backend python -m app.commands.fund.sync_history incremental
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.services.fund.sync.history import FundHistorySyncService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步基金历史数据")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("all", help="同步全部 active 基金历史（全量）")
    subparsers.add_parser("incremental", help="增量同步全部基金历史（推荐日常使用）")
    codes_parser = subparsers.add_parser("codes", help="同步指定基金代码历史")
    codes_parser.add_argument("fund_codes", nargs="+", help="基金代码列表")
    return parser


async def _run(args: argparse.Namespace) -> None:
    async with async_session_factory() as db:
        try:
            service = FundHistorySyncService(db)
            if args.command == "all":
                result = await service.sync_all()
            elif args.command == "incremental":
                result = await service.sync_incremental_all()
            else:
                result = await service.sync_by_fund_codes(args.fund_codes)
            logging.getLogger(__name__).info("基金历史同步结果: %s", result)
        except Exception:
            await db.rollback()
            logging.getLogger(__name__).exception("基金历史同步失败")
            raise
    await close_db()


def main() -> None:
    setup_logging()
    asyncio.run(_run(_build_parser().parse_args()))


if __name__ == "__main__":
    main()
