"""定时任务路由。"""

from fastapi import APIRouter, HTTPException

from app.services.scheduler_service import get_registered_jobs

router = APIRouter(prefix="/cron-tasks", tags=["cron_tasks"])


@router.get("", summary="获取任务列表")
async def list_cron_tasks() -> list[dict]:
    """获取所有定时任务。"""
    return [{**job, "managed_by": "scheduler-worker"} for job in get_registered_jobs()]


# @router.post("", summary="创建定时任务")
# async def create_cron_task(
#     job_id: str = Query(..., description="任务唯一ID"),
#     task_type: str = Query(..., description="任务类型: refresh_quotes / alert_check / news_crawl"),
#     trigger_config: dict = Query(..., description="触发器配置"),
#     params: Optional[dict] = None,
#     enabled: bool = True,
# ) -> dict:
#     """创建一个新的定时任务。"""
#     existing = await scheduler_service.get_job(job_id)
#     if existing:
#         raise HTTPException(status_code=409, detail=f"Job '{job_id}' already exists")
#     return await scheduler_service.add_job(
#         job_id=job_id,
#         task_type=task_type,
#         trigger_config=trigger_config,
#         params=params,
#         enabled=enabled,
#     )


@router.get("/{job_id}", summary="获取任务详情")
async def get_cron_task(job_id: str) -> dict:
    """获取指定定时任务详情。"""
    job = next((job for job in get_registered_jobs() if job["job_id"] == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {**job, "managed_by": "scheduler-worker"}


def _remote_management_not_available() -> None:
    raise HTTPException(
        status_code=503,
        detail="Scheduler runs in a standalone process; cross-process job management is not enabled",
    )


@router.put("/{job_id}/pause", summary="暂停任务")
async def pause_cron_task(job_id: str) -> dict:
    """暂停指定定时任务。"""
    _remote_management_not_available()


@router.put("/{job_id}/resume", summary="恢复任务")
async def resume_cron_task(job_id: str) -> dict:
    """恢复指定定时任务。"""
    _remote_management_not_available()


@router.delete("/{job_id}", summary="删除任务")
async def delete_cron_task(job_id: str) -> dict:
    """删除指定定时任务。"""
    _remote_management_not_available()
