"""Standalone APScheduler process for recurring background jobs."""

import asyncio
import logging
import signal
import sys

from app.core.database import close_db
from app.core.logging import setup_logging
from app.core.redis import close_redis
from app.services.scheduler_service import build_default_jobs, scheduler_service

logger = logging.getLogger(__name__)


async def main() -> None:
    """Register recurring jobs and run until the process receives a stop signal."""
    setup_logging()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signal_name, stop_event.set)
        except (NotImplementedError, RuntimeError):
            signal.signal(signal_name, lambda *_args: loop.call_soon_threadsafe(stop_event.set))

    scheduler_service.start()
    for job in build_default_jobs():
        await scheduler_service.add_job(**job)
    logger.info("Scheduler worker ready: jobs=%s", [job["job_id"] for job in build_default_jobs() if job["enabled"]])

    try:
        await stop_event.wait()
    finally:
        logger.info("Scheduler worker shutting down")
        scheduler_service.shutdown(wait=False)
        await close_redis()
        await close_db()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
