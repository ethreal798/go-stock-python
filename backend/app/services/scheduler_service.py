"""APScheduler 定时任务服务。

负责管理和调度定时任务，如行情刷新、预警检测等。
"""

import asyncio
import logging
import time
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.core.database import async_session_factory
from app.services.news_service import NewsService
from app.services.rag.rag_pipeline_service import RagPipelineService

logger = logging.getLogger(__name__)


def build_default_jobs() -> list[dict]:
    """Return the jobs owned by the standalone scheduler worker."""
    jobs = [
        {
            "job_id": "news_crawl_all",
            "task_type": "news_crawl",
            "trigger_config": {"interval_seconds": settings.NEWS_CRAWL_INTERVAL_SECONDS},
            "params": {"source": "all"},
            "enabled": settings.NEWS_CRAWL_INTERVAL_SECONDS > 0,
        }
    ]
    if settings.RAG_RECONCILE_INTERVAL_SECONDS > 0:
        jobs.append(
            {
                "job_id": "rag_reconcile",
                "task_type": "rag_reconcile",
                "trigger_config": {"interval_seconds": settings.RAG_RECONCILE_INTERVAL_SECONDS},
                "params": {},
                "enabled": True,
            }
        )
    return jobs


class SchedulerService:
    """定时任务调度服务。"""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        self._jobs: dict[str, dict] = {}
        self._rag_pipeline_lock = asyncio.Lock()
        self._last_rag_pipeline_run_at = 0.0

    # ----------------------------------------------------------
    # 调度器生命周期
    # ----------------------------------------------------------

    def start(self) -> None:
        """启动调度器。"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started (timezone=%s)", settings.SCHEDULER_TIMEZONE)

    def shutdown(self, wait: bool = True) -> None:
        """关闭调度器。"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")

    # ----------------------------------------------------------
    # 任务管理
    # ----------------------------------------------------------

    async def add_job(
        self,
        job_id: str,
        task_type: str,
        trigger_config: dict,
        params: Optional[dict] = None,
        enabled: bool = True,
    ) -> dict:
        """添加定时任务。

        Args:
            job_id: 任务唯一 ID
            task_type: 任务类型 (refresh_quotes / alert_check / news_crawl)
            trigger_config: 触发器配置，如 {"interval_seconds": 30} 或 {"cron": "0 9 * * 1-5"}
            params: 任务参数
            enabled: 是否启用
        """
        job_info = {
            "job_id": job_id,
            "task_type": task_type,
            "trigger_config": trigger_config,
            "params": params or {},
            "enabled": enabled,
        }

        if enabled:
            self._schedule_job(job_info)

        self._jobs[job_id] = job_info
        logger.debug("Added job: id=%s, type=%s, enabled=%s", job_id, task_type, enabled)
        return job_info

    async def remove_job(self, job_id: str) -> bool:
        """移除定时任务。"""
        if job_id in self._jobs:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
            del self._jobs[job_id]
            logger.info("Removed job: id=%s", job_id)
            return True
        return False

    async def pause_job(self, job_id: str) -> bool:
        """暂停任务。"""
        if job_id in self._jobs:
            try:
                self._scheduler.pause_job(job_id)
                self._jobs[job_id]["enabled"] = False
                logger.info("Paused job: id=%s", job_id)
                return True
            except Exception:
                return False
        return False

    async def resume_job(self, job_id: str) -> bool:
        """恢复任务。"""
        if job_id in self._jobs:
            try:
                self._scheduler.resume_job(job_id)
                self._jobs[job_id]["enabled"] = True
                logger.info("Resumed job: id=%s", job_id)
                return True
            except Exception:
                return False
        return False

    async def list_jobs(self) -> list[dict]:
        """列出所有任务。"""
        return list(self._jobs.values())

    async def get_job(self, job_id: str) -> Optional[dict]:
        """获取单个任务信息。"""
        return self._jobs.get(job_id)

    # ----------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------

    def _schedule_job(self, job_info: dict) -> None:
        """实际注册任务到调度器。"""
        job_id = job_info["job_id"]
        trigger_config = job_info["trigger_config"]
        task_type = job_info["task_type"]

        # 根据配置创建触发器
        if "interval_seconds" in trigger_config:
            trigger = IntervalTrigger(seconds=trigger_config["interval_seconds"])
        elif "cron" in trigger_config:
            trigger = CronTrigger.from_crontab(trigger_config["cron"])
        else:
            logger.warning("Unknown trigger config for job %s: %s", job_id, trigger_config)
            return

        self._scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            id=job_id,
            args=[task_type, job_info.get("params", {})],
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

    async def _execute_task(self, task_type: str, params: dict) -> None:
        """执行定时任务的统一入口。"""
        started_at = time.perf_counter()
        logger.debug("Executing task: type=%s, params=%s", task_type, params)

        async with async_session_factory() as db:
            try:
                if task_type == "refresh_quotes":
                    pass
                elif task_type == "alert_check":
                    pass
                elif task_type == "news_crawl":
                    total_new_count = await self._execute_news_crawl(db, params)
                    if total_new_count > 0:
                        await self._run_rag_pipeline_after_news_crawl(db, params, total_new_count)
                elif task_type == "rag_reconcile":
                    await self._run_rag_reconcile(db, params)

                await db.commit()
            except Exception:
                logger.exception(
                    "Task failed: type=%s duration_ms=%.2f", task_type, (time.perf_counter() - started_at) * 1000
                )
                await db.rollback()

    async def _execute_news_crawl(self, db, params: dict) -> int:
        service = NewsService(db)
        source = params.get("source", "all")

        if source == "all":
            results = await service.fetch_all_sources()
            total_new_count = sum(results.values())
            log = logger.info if total_new_count > 0 else logger.debug
            log("News crawl completed: source=all, total_new_count=%s, results=%s", total_new_count, results)
            return total_new_count

        news_type = params.get("type", "fast")
        total_new_count = await service.fetch_remote_news(source, type=news_type)
        log = logger.info if total_new_count > 0 else logger.debug
        log("News crawl completed: source=%s, total_new_count=%s", source, total_new_count)
        return total_new_count

    async def _run_rag_pipeline_after_news_crawl(self, db, params: dict, total_new_count: int) -> None:
        if not settings.RAG_PIPELINE_ON_NEWS_CRAWL:
            logger.debug("Skip RAG pipeline after news crawl: disabled")
            return

        await self._run_rag_pipeline_drain(db, params, reason="news_crawl", total_new_count=total_new_count)

    async def _run_rag_reconcile(self, db, params: dict) -> None:
        await self._run_rag_pipeline_drain(db, params, reason="reconcile")

    async def _run_rag_pipeline_drain(
        self,
        db,
        params: dict,
        *,
        reason: str,
        total_new_count: int | None = None,
    ) -> None:
        if self._rag_pipeline_lock.locked():
            logger.debug("Skip RAG pipeline: previous pipeline is still running, reason=%s", reason)
            return

        now = time.monotonic()
        elapsed = now - self._last_rag_pipeline_run_at
        # 当执行任务间隔小于配置的RAG流水线间隔的最小时间，则不执行流水线作业
        if elapsed < settings.RAG_PIPELINE_MIN_INTERVAL_SECONDS:
            logger.debug(
                "Skip RAG pipeline: min interval not reached, reason=%s, elapsed=%.2fs, required=%ss",
                reason,
                elapsed,
                settings.RAG_PIPELINE_MIN_INTERVAL_SECONDS,
            )
            return

        async with self._rag_pipeline_lock:
            self._last_rag_pipeline_run_at = time.monotonic()
            pipeline_service = RagPipelineService(db)
            result = await pipeline_service.run_news_pipeline_drain(
                max_batches=params.get("rag_drain_max_batches", settings.RAG_PIPELINE_DRAIN_MAX_BATCHES),
                max_seconds=params.get("rag_drain_max_seconds", settings.RAG_PIPELINE_DRAIN_MAX_SECONDS),
                news_limit=params.get("rag_news_limit", settings.RAG_PIPELINE_NEWS_LIMIT),
                news_type=params.get("rag_news_type", "all"),
                relevant_only=params.get("rag_relevant_only", True),
                chunk_limit=params.get("rag_chunk_limit", settings.RAG_PIPELINE_CHUNK_LIMIT),
                max_chars=params.get("rag_max_chars", settings.RAG_PIPELINE_MAX_CHARS),
                overlap_chars=params.get("rag_overlap_chars", settings.RAG_PIPELINE_OVERLAP_CHARS),
                embed_limit=params.get("rag_embed_limit", settings.RAG_PIPELINE_EMBED_LIMIT),
                embedding_model=params.get("rag_embedding_model"),
            )

            if result["success"]:
                logger.info(
                    "RAG pipeline completed: reason=%s, total_new_count=%s, result=%s",
                    reason,
                    total_new_count,
                    result,
                )
                return

            logger.warning(
                "RAG pipeline failed: reason=%s, total_new_count=%s, failed_stage=%s, error=%s, result=%s",
                reason,
                total_new_count,
                result["failed_stage"],
                result["error"],
                result,
            )


# 全局调度器实例
scheduler_service = SchedulerService()
