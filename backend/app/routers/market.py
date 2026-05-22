"""行情数据路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/market", tags=["market"])


def get_market_service(db: AsyncSession = Depends(get_db)) -> MarketDataService:
    return MarketDataService(db)


@router.get("/hot-stocks", summary="热门股票排行")
async def get_hot_stocks(
    market: str = Query("a", description="市场类型: a / sh / sz"),
    count: int = Query(10, ge=1, le=100, description="返回数量"),
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取热门股票排行榜。"""
    return await service.get_hot_stocks(market=market, count=count)


@router.get("/dragon-tiger", summary="龙虎榜")
async def get_dragon_tiger(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD"),
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取龙虎榜数据。"""
    return await service.get_dragon_tiger(date=date)


@router.get("/statistics", summary="市场统计")
async def get_market_statistics(
    service: MarketDataService = Depends(get_market_service),
) -> dict:
    """获取市场统计数据（涨跌家数、成交量等）。"""
    return await service.get_market_statistics()


@router.get("/industry-sectors", summary="行业板块")
async def get_industry_sectors(
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取行业板块列表及涨跌情况。"""
    return await service.get_industry_sectors()


@router.get("/concept-sectors", summary="概念板块")
async def get_concept_sectors(
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取概念板块列表及涨跌情况。"""
    return await service.get_concept_sectors()


@router.get("/global-indexes", summary="全球指数")
async def get_global_indexes(
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取全球主要指数行情。"""
    return await service.get_global_indexes()


@router.get("/margin-trading", summary="融资融券")
async def get_margin_trading(
    code: Optional[str] = Query(None, description="股票代码，为空则返回全部"),
    service: MarketDataService = Depends(get_market_service),
) -> list[dict]:
    """获取融资融券数据。"""
    return await service.get_margin_trading(code=code)
