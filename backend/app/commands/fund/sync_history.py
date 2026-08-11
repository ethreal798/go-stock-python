"""命令行历史同步入口。

示例::

    python -m app.commands.fund.sync_history --category open --limit 5
    python -m app.commands.fund.sync_history --category all
"""

# 允许在类型注解中使用前置引用（即类名在定义之前就能被用于类型提示），这是 Python 3.7+ 为了支持延迟类型评估的常用写法。
from __future__ import annotations

# 用于解析命令行参数
import argparse
import asyncio
import logging
from datetime import date

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.services.fund.sync.history import FundHistorySyncService


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期格式必须为 YYYY-MM-DD") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="同步开放式/LOF、场内ETF净值和货币基金收益历史")
    parser.add_argument(
        "--category",
        choices=("open", "money", "exchange", "all"),
        default="all",
        help="同步分类，默认 all",
    )
    parser.add_argument(
        "--fund-code",
        action="append",
        dest="fund_codes",
        help="只同步指定代码，可重复传入；不传则同步 active 基金",
    )
    parser.add_argument("--start-date", type=_parse_date, help="起始日期，默认结束日期前三年")
    parser.add_argument("--end-date", type=_parse_date, help="结束日期，默认今天")
    parser.add_argument("--limit", type=int, help="限制本次同步基金数量，建议先用于小样本验证")
    parser.add_argument("--concurrency", type=int, default=4, help="数据源并发数，默认 4")
    parser.add_argument("--batch-size", type=int, default=20, help="每批基金数，默认 20")
    parser.add_argument("--retries", type=int, default=2, help="单只基金失败重试次数，默认 2")
    return parser


async def _run(args: argparse.Namespace) -> None:
    # 1. 处理分类参数
    categories = ("open", "money", "exchange") if args.category == "all" else (args.category,)
    # 2. 创建数据库会话
    async with async_session_factory() as db:
        try:
            # 3. 调用核心服务
            result = await FundHistorySyncService(db).fetch_and_sync(
                categories=categories,
                start_date=args.start_date,
                end_date=args.end_date,
                fund_codes=args.fund_codes,
                limit=args.limit,
                concurrency=args.concurrency,
                batch_size=args.batch_size,
                retries=args.retries,
            )
            # 4. 记录成功日志
            logging.getLogger(__name__).info("基金历史同步结果: %s", result)
        except Exception:
            # 5. 异常处理：回滚事务
            await db.rollback()
            logging.getLogger(__name__).exception("基金历史同步失败")
            raise
    # 6. 关闭数据库连接
    await close_db()


def main() -> None:
    setup_logging()  # 初始化日志配置
    args = _build_parser().parse_args()  # 解析命令行参数
    asyncio.run(_run(args))  # 启动事件循环，运行异步主逻辑


if __name__ == "__main__":
    main()
