"""股票相关路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stock import (
    StockCreate,
    StockRealTimePrice,
    StockResponse,
    StockSearchResult,
)
from app.services.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


def get_stock_service(db: AsyncSession = Depends(get_db)) -> StockService:
    return StockService(db)


@router.get("", response_model=list[StockResponse], summary="获取关注股票列表")
async def list_followed_stocks(
    group: Optional[str] = Query(None, description="分组名称"),
    service: StockService = Depends(get_stock_service),
) -> list[StockResponse]:
    """获取当前用户关注的股票列表。"""
    stocks = await service.get_followed_stocks(group=group)
    return stocks  # type: ignore[return-value]


@router.get("/search", response_model=list[StockSearchResult], summary="搜索股票")
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    service: StockService = Depends(get_stock_service),
) -> list[StockSearchResult]:
    """根据代码、名称或拼音搜索股票。"""
    return await service.search_stocks(keyword=keyword, limit=limit)


@router.get("/{code}/realtime", response_model=StockRealTimePrice, summary="获取实时行情")
async def get_realtime_price(
    code: str,
    service: StockService = Depends(get_stock_service),
) -> StockRealTimePrice:
    """获取指定股票的实时行情数据。"""
    result = await service.get_realtime_price(code=code)
    return result  # type: ignore[return-value]


@router.post("/follow", response_model=StockResponse, summary="添加关注")
async def follow_stock(
    stock: StockCreate,
    service: StockService = Depends(get_stock_service),
) -> StockResponse:
    """添加一只股票到关注列表。"""
    result = await service.follow_stock(
        code=stock.code, name=stock.name, group=stock.group_name
    )
    return result  # type: ignore[return-value]


@router.delete("/follow/{stock_id}", summary="取消关注")
async def unfollow_stock(
    stock_id: int,
    service: StockService = Depends(get_stock_service),
) -> dict:
    """取消关注指定股票。"""
    success = await service.unfollow_stock(stock_id=stock_id)
    return {"success": success}
