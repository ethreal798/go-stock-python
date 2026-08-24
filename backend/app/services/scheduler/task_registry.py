"""定时任务装饰器注册表。

提供类似 Celery 的装饰器注册模式，让任务定义自描述、自注册。

用法::

    # 在 tasks/news_crawl.py 中
    from app.services.scheduler.task_registry import register_task

    @register_task(
        task_id="news_crawl",
        trigger_config_key="NEWS_CRAWL_INTERVAL_SECONDS",
        enabled_key="NEWS_CRAWL_ENABLED",
    )
    async def news_crawl(db, params):
        ...

    # 在 tasks/__init__.py 中统一导入
    from .news_crawl import *
    from .rag_reconcile import *

    # 调度器启动时从 registry 查询所有任务
    from app.services.scheduler.task_registry import get_all_tasks
    tasks = get_all_tasks()
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# 任务注册表：task_id → 任务元数据 + handler
_task_registry: dict[str, dict[str, Any]] = {}


def register_task(
    task_id: str,
    *,
    trigger_config: Optional[dict[str, Any]] = None,
    trigger_config_key: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    params_key: Optional[str] = None,
    enabled: bool = True,
    enabled_key: Optional[str] = None,
    depends_on: Optional[list[str]] = None,
) -> Callable:
    """装饰器：将一个异步函数注册为定时任务。

    Args:
        task_id: 任务唯一标识，如 ``"news_crawl"``
        trigger_config: 静态触发配置，如 ``{"interval_seconds": 60}``
        trigger_config_key: 从 ``settings`` 动态读取触发配置的 key，
            如 ``"NEWS_CRAWL_INTERVAL_SECONDS"``，值为 int 时自动转为
            ``{"interval_seconds": value}``，值为 str 时自动转为
            ``{"cron": value}``
        params: 静态任务参数
        params_key: 从 ``settings`` 动态读取任务参数的 key（dict）
        enabled: 静态启用开关
        enabled_key: 从 ``settings`` 动态读取启用开关的 key
        depends_on: 依赖的其他任务 ID 列表，当前任务将在依赖任务完成后执行

    Returns:
        原函数，保持可调用
    """

    def decorator(func: Callable) -> Callable:
        if task_id in _task_registry:
            logger.warning(
                "Task '%s' already registered, overwriting. Previous: %s",
                task_id,
                _task_registry[task_id].get("handler"),
            )

        _task_registry[task_id] = {
            "task_id": task_id,
            "trigger_config": trigger_config,
            "trigger_config_key": trigger_config_key,
            "params": params,
            "params_key": params_key,
            "enabled": enabled,
            "enabled_key": enabled_key,
            "depends_on": depends_on or [],
            "handler": func,
        }
        logger.debug("Registered task: id=%s, handler=%s", task_id, func.__name__)
        return func

    return decorator


def _resolve_trigger_config(entry: dict[str, Any]) -> Optional[dict[str, Any]]:
    """解析触发配置，支持静态值和 settings 动态值。"""
    # 优先使用动态 key
    key = entry.get("trigger_config_key")
    if key:
        value = getattr(settings, key, None)
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return {"interval_seconds": value}
        if isinstance(value, str):
            return {"cron": value}
        return None

    # 使用静态配置
    return entry.get("trigger_config")


def _resolve_enabled(entry: dict[str, Any]) -> bool:
    """解析启用开关。"""
    key = entry.get("enabled_key")
    if key:
        value = getattr(settings, key, None)
        if value is not None:
            return bool(value)
    return entry.get("enabled", True)


def _resolve_params(entry: dict[str, Any]) -> dict[str, Any]:
    """解析任务参数。"""
    key = entry.get("params_key")
    if key:
        value = getattr(settings, key, None)
        if isinstance(value, dict):
            return value
    return entry.get("params") or {}


def get_all_tasks() -> list[dict[str, Any]]:
    """获取所有已注册的任务列表（已解析 settings 值）。

    Returns:
        每个元素为包含 ``job_id``、``task_type``、``trigger_config``、
        ``params``、``enabled``、``depends_on`` 字段的字典，
        可直接用于 ``SchedulerService.add_job()``。
    """
    result = []
    for task_id, entry in _task_registry.items():
        trigger_config = _resolve_trigger_config(entry)
        if trigger_config is None:
            logger.debug("Skipping task '%s': no trigger config", task_id)
            continue

        result.append(
            {
                "job_id": task_id,
                "task_type": task_id,
                "trigger_config": trigger_config,
                "params": _resolve_params(entry),
                "enabled": _resolve_enabled(entry),
                "depends_on": entry.get("depends_on", []),
            }
        )
    return result


def get_handler(task_id: str) -> Optional[Callable]:
    """获取指定任务的 handler 函数。"""
    entry = _task_registry.get(task_id)
    if entry is None:
        return None
    return entry.get("handler")


def get_task_entry(task_id: str) -> Optional[dict[str, Any]]:
    """获取指定任务的原始注册表条目。"""
    return _task_registry.get(task_id)


def list_registered_task_ids() -> list[str]:
    """列出所有已注册的任务 ID（仅用于调试）。"""
    return list(_task_registry.keys())
