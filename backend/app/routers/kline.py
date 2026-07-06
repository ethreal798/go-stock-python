"""K线数据路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.stock_service import StockService

router = APIRouter(prefix="/kline", tags=["kline"])


def get_stock_service(db: AsyncSession = Depends(get_db)) -> StockService:
    return StockService(db)


@router.get("/{code}", summary="获取K线数据")
async def get_kline(
    code: str,
    source: str = Query("eastmoney", description="数据源: eastmoney / sina / tdx"),
    period: str = Query("daily", description="周期: daily / weekly / monthly / 60min / 30min / 15min / 5min"),
    count: int = Query(120, ge=1, le=1000, description="返回条数"),
    service: StockService = Depends(get_stock_service),
) -> list[dict]:
    """获取指定股票的K线数据，支持多数据源和多周期。"""
    return await service.get_kline(code=code, source=source, period=period, count=count)
