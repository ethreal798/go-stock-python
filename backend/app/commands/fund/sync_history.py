"""命令行基金历史同步入口。

示例：
    python -m app.commands.fund.sync_history --all
    python -m app.commands.fund.sync_history --codes 007339

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
    subparsers.add_parser("all", help="同步全部 active 基金历史")
    codes_parser = subparsers.add_parser("codes", help="同步指定基金代码历史")
    codes_parser.add_argument("fund_codes", nargs="+", help="基金代码列表")
    return parser


async def _run(args: argparse.Namespace) -> None:
    async with async_session_factory() as db:
        try:
            service = FundHistorySyncService(db)
            if args.command == "all":
                result = await service.sync_all()
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
