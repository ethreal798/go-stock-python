"""基金目录（catalog）同步命令行入口。

同步全量基金代码、名称、类型，以及 is_hb / is_exchange 标记。

开发环境运行：
    cd backend
    python -m app.commands.fund.sync_catalog

Docker 容器中运行：
    # 开发模式（容器已启动，挂载了本地代码）
    docker compose exec backend python -m app.commands.fund.sync_catalog

    # 生产模式（临时启动一个容器执行后退出）
    docker compose run --rm backend python -m app.commands.fund.sync_catalog
"""

import asyncio
import logging

from app.core.database import async_session_factory, close_db
from app.core.logging import setup_logging
from app.services.fund.sync.catalog import FundCatalogSyncService


async def main() -> None:
    setup_logging()
    async with async_session_factory() as db:
        try:
            await FundCatalogSyncService(db).fetch_and_sync()
            await db.commit()
        except Exception:
            await db.rollback()
            logging.getLogger(__name__).exception("基金目录同步失败")
            raise
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
