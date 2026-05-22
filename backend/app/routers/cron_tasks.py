"""定时任务路由。"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/cron-tasks", tags=["cron_tasks"])


@router.get("", summary="获取任务列表")
async def list_cron_tasks() -> list[dict]:
    """获取所有定时任务。"""
    return await scheduler_service.list_jobs()


@router.post("", summary="创建定时任务")
async def create_cron_task(
    job_id: str = Query(..., description="任务唯一ID"),
    task_type: str = Query(..., description="任务类型: refresh_quotes / alert_check / news_crawl"),
    trigger_config: dict = Query(..., description="触发器配置"),
    params: Optional[dict] = None,
    enabled: bool = True,
) -> dict:
    """创建一个新的定时任务。"""
    existing = await scheduler_service.get_job(job_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Job '{job_id}' already exists")
    return await scheduler_service.add_job(
        job_id=job_id,
        task_type=task_type,
        trigger_config=trigger_config,
        params=params,
        enabled=enabled,
    )


@router.get("/{job_id}", summary="获取任务详情")
async def get_cron_task(job_id: str) -> dict:
    """获取指定定时任务详情。"""
    job = await scheduler_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.put("/{job_id}/pause", summary="暂停任务")
async def pause_cron_task(job_id: str) -> dict:
    """暂停指定定时任务。"""
    success = await scheduler_service.pause_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {"success": True}


@router.put("/{job_id}/resume", summary="恢复任务")
async def resume_cron_task(job_id: str) -> dict:
    """恢复指定定时任务。"""
    success = await scheduler_service.resume_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {"success": True}


@router.delete("/{job_id}", summary="删除任务")
async def delete_cron_task(job_id: str) -> dict:
    """删除指定定时任务。"""
    success = await scheduler_service.remove_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {"success": True}
