"""APScheduler 定时任务服务。

负责管理和调度定时任务，如行情刷新、预警检测等。
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务。"""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        self._jobs: dict[str, dict] = {}

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
        logger.info("Added job: id=%s, type=%s, enabled=%s", job_id, task_type, enabled)
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
        )

    @staticmethod
    async def _execute_task(task_type: str, params: dict) -> None:
        """执行定时任务的统一入口。"""
        logger.info("Executing task: type=%s, params=%s", task_type, params)
        # TODO: 根据 task_type 分发到具体执行逻辑
        if task_type == "refresh_quotes":
            pass  # await stock_service.refresh_all_quotes()
        elif task_type == "alert_check":
            pass  # await alert_service.check_alerts()
        elif task_type == "news_crawl":
            pass  # await news_service.crawl_latest_news()


# 全局调度器实例
scheduler_service = SchedulerService()
