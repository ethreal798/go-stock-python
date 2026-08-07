"""命令行同步入口：python -m app.services.fund.sync_rankings。"""

import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.services.fund.ranking_sync import FundRankingSyncService


async def main() -> None:
    setup_logging()
    async with async_session_factory() as db:
        try:
            result = await FundRankingSyncService(db).fetch_and_sync()
            await db.commit()
            logging.getLogger(__name__).info("同步结果: %s", result)
        except Exception:
            await db.rollback()
            logging.getLogger(__name__).exception("基金排行同步失败")
            raise
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
