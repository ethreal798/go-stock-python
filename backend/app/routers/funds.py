"""基金相关路由。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.fund import (
    FundPerformanceTrendResponse,
    FundRankCategory,
    FundRankListResponse,
    FundRankOrder,
    FundRankPeriod,
    FundRankSortField,
    FundResponse,
    FundTrendPeriod,
    FundWatchlistItemCreate,
    FundWatchlistItemResponse,
)
from app.services.fund.command.watchlist import FundNotFoundError, FundWatchlistCommandService
from app.services.fund.query.catalog import FundCatalogQueryService
from app.services.fund.query.ranking import FundRankingQueryService
from app.services.fund.query.watchlist import FundWatchlistQueryService
from app.services.fund.query.performance_trend import (
    FundPerformanceTrendNotFoundError,
    FundPerformanceTrendQueryService,
    FundPerformanceTrendUnavailableError,
    FundPerformanceTrendUnsupportedError,
)
from app.services.fund.sync.ranking import FundRankingSyncService
from app.services.user_service import UserService
from app.routers.auth import oauth2_scheme, get_user_service
from app.models.user import User

router = APIRouter(prefix="/funds", tags=["funds"])


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """获取当前登录用户的依赖项。"""
    return await user_service.get_current_user(token)


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Optional[User]:
    """获取当前登录用户的依赖项（可选）。"""
    if not token:
        return None
    try:
        return await user_service.get_current_user(token)
    except Exception:
        return None


def get_fund_catalog_query_service(db: AsyncSession = Depends(get_db)) -> FundCatalogQueryService:
    return FundCatalogQueryService(db)


def get_fund_watchlist_query_service(db: AsyncSession = Depends(get_db)) -> FundWatchlistQueryService:
    return FundWatchlistQueryService(db)


def get_fund_watchlist_command_service(db: AsyncSession = Depends(get_db)) -> FundWatchlistCommandService:
    return FundWatchlistCommandService(db)


def get_fund_performance_trend_service(
    db: AsyncSession = Depends(get_db),
) -> FundPerformanceTrendQueryService:
    return FundPerformanceTrendQueryService(db)


def get_fund_ranking_sync_service(db: AsyncSession = Depends(get_db)) -> FundRankingSyncService:
    return FundRankingSyncService(db)


def get_fund_ranking_query_service(db: AsyncSession = Depends(get_db)) -> FundRankingQueryService:
    return FundRankingQueryService(db)


@router.get("/search", response_model=List[FundResponse], summary="搜索基金", response_model_exclude_unset=True)
async def search_funds(
    keyword: str = Query(..., description="搜索关键词(代码/名称)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    service: FundCatalogQueryService = Depends(get_fund_catalog_query_service),
) -> List[FundResponse]:
    """搜索基金，支持代码和名称模糊匹配。"""
    user_id = current_user.id if current_user else None
    return await service.search_funds(keyword=keyword, page=page, limit=limit, user_id=user_id)


# ============================================================
# 自选基金相关
# ============================================================


@router.get(
    "/watchlist",
    response_model=List[FundWatchlistItemResponse],
    summary="获取基金自选列表",
    response_model_exclude_unset=True,
)
async def get_fund_watchlist(
    current_user: User = Depends(get_current_user),
    service: FundWatchlistQueryService = Depends(get_fund_watchlist_query_service),
) -> List[FundWatchlistItemResponse]:
    """获取当前用户的基金自选项及其最新行情。"""
    return await service.get_watchlist(current_user.id)


@router.post("/watchlist", response_model=FundWatchlistItemResponse, summary="加入基金自选")
async def add_fund_to_watchlist(
    fund_in: FundWatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    service: FundWatchlistCommandService = Depends(get_fund_watchlist_command_service),
) -> FundWatchlistItemResponse:
    """将基金加入自选列表。"""
    try:
        return await service.add_to_watchlist(
            user_id=current_user.id,
            fund_code=fund_in.fund_code,
            remark=fund_in.remark,
        )
    except FundNotFoundError as exc:
        raise HTTPException(status_code=404, detail="基金不存在") from exc


@router.delete("/watchlist/{code}", summary="移出基金自选")
async def remove_fund_from_watchlist(
    code: str,
    current_user: User = Depends(get_current_user),
    service: FundWatchlistCommandService = Depends(get_fund_watchlist_command_service),
) -> dict:
    """从自选列表中移除基金。"""
    success = await service.remove_from_watchlist(current_user.id, code)
    if not success:
        raise HTTPException(status_code=404, detail="基金自选记录不存在")
    return {"message": "ok"}


# ============================================================
# 基金详情相关
# ============================================================


@router.get(
    "/{code}/performance-trend",
    response_model=FundPerformanceTrendResponse,
    summary="获取基金累计收益率走势",
)
async def get_fund_performance_trend(
    code: str,
    period: FundTrendPeriod = Query("1y", description="走势周期"),
    service: FundPerformanceTrendQueryService = Depends(get_fund_performance_trend_service),
) -> FundPerformanceTrendResponse:
    """返回一只开放式基金指定周期的最新绘图快照。"""
    try:
        return await service.get_trend(code, period)
    except FundPerformanceTrendNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Fund not found") from exc
    except FundPerformanceTrendUnsupportedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ValueError, FundPerformanceTrendUnavailableError) as exc:
        status_code = 400 if isinstance(exc, ValueError) else 503
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{code}", response_model=FundResponse, summary="获取基金详情", response_model_exclude_unset=True)
async def get_fund_detail(
    code: str,
    service: FundCatalogQueryService = Depends(get_fund_catalog_query_service),
) -> FundResponse:
    """获取指定基金身份和对应排行最新指标。"""
    fund = await service.get_fund_detail(code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund


@router.post("/sync", summary="同步基金排行最新数据")
async def sync_funds(
    service: FundRankingSyncService = Depends(get_fund_ranking_sync_service),
) -> dict:
    """手动触发开放式、场内交易和货币型基金排行同步。"""
    counts = await service.fetch_and_sync()
    return {"message": "基金排行同步完成", "counts": counts}


@router.get("/", response_model=FundRankListResponse, summary="获取基金排行", response_model_exclude_unset=True)
async def get_funds(
    category: FundRankCategory = Query("open", description="基金分类: open/money/exchange"),
    sort: FundRankSortField = Query("1y", description="排序字段"),
    period: Optional[FundRankPeriod] = Query(None, description="显示周期，不传时由 sort 推导"),
    order: FundRankOrder = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    fund_type: Optional[str] = Query(None, description="基金类型过滤"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    service: FundRankingQueryService = Depends(get_fund_ranking_query_service),
) -> FundRankListResponse:
    """获取基金排行列表，支持分类、排序、分页。"""
    user_id = current_user.id if current_user else None
    try:
        return await service.get_rankings(
            category=category,
            sort=sort,
            period=period,
            order=order,
            page=page,
            limit=limit,
            fund_type=fund_type,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
