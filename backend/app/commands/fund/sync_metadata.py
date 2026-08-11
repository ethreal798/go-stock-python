"""基金档案与风险指标同步命令行入口。"""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.services.fund.sync.metadata import FundMetadataSyncService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步雪球基金档案和风险指标最新值")
    parser.add_argument("--content", choices=("profile", "risk", "all"), default="all")
    parser.add_argument("--category", choices=("open", "money", "exchange", "all"), default="all")
    parser.add_argument("--fund-code", action="append", dest="fund_codes", help="只同步指定代码，可重复传入")
    parser.add_argument("--limit", type=int, help="限制本次同步基金数量")
    parser.add_argument("--concurrency", type=int, default=4, help="数据源并发数，默认 4")
    parser.add_argument("--batch-size", type=int, default=20, help="每批基金数，默认 20")
    parser.add_argument("--retries", type=int, default=2, help="单接口失败重试次数，默认 2")
    parser.add_argument("--timeout", type=float, default=20, help="单次雪球请求超时秒数，默认 20")
    return parser


async def _run(args: argparse.Namespace) -> None:
    categories = ("open", "money", "exchange") if args.category == "all" else (args.category,)
    async with async_session_factory() as db:
        try:
            result = await FundMetadataSyncService(db).fetch_and_sync(
                categories=categories,
                sync_profile=args.content in {"profile", "all"},
                sync_risk=args.content in {"risk", "all"},
                fund_codes=args.fund_codes,
                limit=args.limit,
                concurrency=args.concurrency,
                batch_size=args.batch_size,
                retries=args.retries,
                timeout=args.timeout,
            )
            logging.getLogger(__name__).info("基金档案与风险指标同步结果: %s", result)
        except Exception:
            await db.rollback()
            logging.getLogger(__name__).exception("基金档案与风险指标同步失败")
            raise
    await close_db()


def main() -> None:
    setup_logging()
    asyncio.run(_run(_build_parser().parse_args()))


if __name__ == "__main__":
    main()
