"""RAG 对账定时任务。"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.services.scheduler.task_registry import register_task
from app.services.scheduler.tasks.news_crawl import _run_rag_pipeline_drain

logger = logging.getLogger(__name__)


@register_task(
    task_id="rag_reconcile",
    trigger_config_key="RAG_RECONCILE_INTERVAL_SECONDS",
    enabled_key="RAG_PIPELINE_SWITCH",
)
async def rag_reconcile(db, params: dict[str, Any]) -> None:
    """RAG 对账定时任务。

    定期触发 RAG 流水线 drain，确保知识库与最新新闻保持同步。
    """
    await _run_rag_pipeline_drain(db, params, reason="reconcile")
