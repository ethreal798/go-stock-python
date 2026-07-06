"""新闻资讯路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.sse import sse_manager
from app.schemas.news import TelegraphResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


def get_news_service(db: AsyncSession = Depends(get_db)) -> NewsService:
    return NewsService(db)


@router.get("/telegraph", response_model=list[TelegraphResponse], summary="7x24快讯")
async def get_telegraph(
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    page: int = Query(1, ge=1, description="页码"),
    source: str = Query("all", description="数据源: all / eastmoney / cls / wscn / sina"),
    relevant_only: bool = Query(True, description="仅返回金融相关新闻"),
    service: NewsService = Depends(get_news_service),
) -> list[TelegraphResponse]:
    """获取7x24小时财经快讯(从数据库读取)。"""

    return await service.get_telegraphs(source=source, limit=count, page=page, relevant_only=relevant_only)


@router.get("/stream", summary="新闻实时通知流 (SSE)")
async def news_stream():
    """SSE 端点，当有新新闻入库时发送 'refresh' 信号。"""
    return StreamingResponse(
        sse_manager.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )


@router.get("/market", response_model=list[TelegraphResponse], summary="市场要闻")
async def get_market_news(
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    page: int = Query(1, ge=1, description="页码"),
    relevant_only: bool = Query(True, description="仅返回金融相关新闻"),
    service: NewsService = Depends(get_news_service),
) -> list[TelegraphResponse]:
    """获取市场重要新闻资讯（从数据库读取）。"""
    return await service.get_telegraphs(type="news", limit=count, page=page, relevant_only=relevant_only)


@router.get("/stock/{code}", summary="个股新闻")
async def get_stock_news(
    code: str,
    count: int = Query(10, ge=1, le=50, description="返回数量"),
) -> list[dict]:
    """获取指定股票相关新闻。"""
    # TODO: 调用新闻服务
    return []


@router.get("/research/{code}", summary="研报")
async def get_research_reports(
    code: str,
    count: int = Query(10, ge=1, le=50, description="返回数量"),
) -> list[dict]:
    """获取指定股票的研究报告。"""
    # TODO: 调用研报服务
    return []
