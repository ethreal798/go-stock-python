"""多源财经快讯路由。"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.sse import sse_manager
from app.schemas.news import (
    NewsListResponse,
    NewsOverviewResponse,
    NewsSourceResponse,
    NewsUpdatesResponse,
)
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


def get_news_service(db: AsyncSession = Depends(get_db)) -> NewsService:
    return NewsService(db)


@router.get("/sources", response_model=list[NewsSourceResponse], summary="快讯来源")
async def list_news_sources(service: NewsService = Depends(get_news_service)) -> list[NewsSourceResponse]:
    return await service.list_sources()


@router.get("/flash/overview", response_model=NewsOverviewResponse, summary="快讯概览与热门主题")
async def get_flash_overview(
    period: Literal["today", "week", "all"] = Query("today", description="today/week/all"),
    source: Literal["cls", "wscn", "sina"] = Query("cls", description="数据源，默认财联社"),
    topic_limit: int = Query(10, ge=1, le=50),
    service: NewsService = Depends(get_news_service),
) -> NewsOverviewResponse:
    return await service.get_overview(source=source, period=period, topic_limit=topic_limit)


@router.get("/flash", response_model=NewsListResponse, summary="分来源快讯列表")
async def list_flash_news(
    source: Literal["cls", "wscn", "sina"] = Query("cls", description="数据源，默认财联社"),
    period: Literal["today", "week", "all"] = Query("today", description="today/week/all"),
    important_only: bool = Query(False, description="只看来源标记的重要快讯"),
    topic_name: str | None = Query(None, min_length=1, max_length=200, description="主题名"),
    cursor_time: datetime | None = Query(None),
    cursor_id: int | None = Query(None, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
) -> NewsListResponse:
    if (cursor_time is None) != (cursor_id is None):
        raise HTTPException(status_code=422, detail="cursor_time 和 cursor_id 必须同时提供")
    return await service.list_flash_news(
        source=source,
        period=period,
        important_only=important_only,
        topic_name=topic_name,
        cursor_time=cursor_time,
        cursor_id=cursor_id,
        limit=limit,
    )


@router.get("/stream", summary="快讯实时通知流 (SSE)")
async def news_stream():
    return StreamingResponse(
        sse_manager.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )


@router.get("/flash/updates", response_model=NewsUpdatesResponse, summary="增量快讯列表")
async def list_flash_updates(
    after_id: int = Query(..., ge=0, description="上次同步响应返回的 sync_id"),
    source: Literal["cls", "wscn", "sina"] = Query("cls", description="数据源，默认财联社"),
    period: Literal["today", "week", "all"] = Query("today", description="today/week/all"),
    important_only: bool = Query(False, description="只看来源标记的重要快讯"),
    topic_name: str | None = Query(None, min_length=1, max_length=200, description="主题名"),
    limit: int = Query(100, ge=1, le=200),
    service: NewsService = Depends(get_news_service),
) -> NewsUpdatesResponse:
    return await service.list_flash_updates(
        source=source,
        after_id=after_id,
        period=period,
        important_only=important_only,
        topic_name=topic_name,
        limit=limit,
    )
