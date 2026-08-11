"""基金相关路由。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.fund import (
    FundPerformanceTrendResponse,
    FundResponse,
    FundTrendPeriod,
    FollowedFundResponse,
    FollowedFundCreate,
)
from app.services.fund.command.follow import FundFollowCommandService, FundNotFoundError
from app.services.fund.query.catalog import FundCatalogQueryService
from app.services.fund.query.followed import FundFollowedQueryService
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


def get_fund_followed_query_service(db: AsyncSession = Depends(get_db)) -> FundFollowedQueryService:
    return FundFollowedQueryService(db)


def get_fund_follow_command_service(db: AsyncSession = Depends(get_db)) -> FundFollowCommandService:
    return FundFollowCommandService(db)


def get_fund_performance_trend_service(
    db: AsyncSession = Depends(get_db),
) -> FundPerformanceTrendQueryService:
    return FundPerformanceTrendQueryService(db)


def get_fund_ranking_sync_service(db: AsyncSession = Depends(get_db)) -> FundRankingSyncService:
    return FundRankingSyncService(db)


@router.get("/", response_model=List[FundResponse], summary="获取基金列表")
async def get_funds(
    keyword: Optional[str] = Query(None, description="搜索关键词(代码/名称)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    service: FundCatalogQueryService = Depends(get_fund_catalog_query_service),
) -> List[FundResponse]:
    """获取全量基金列表，支持模糊搜索。"""
    user_id = current_user.id if current_user else None
    return await service.get_funds(keyword=keyword, page=page, limit=limit, user_id=user_id)


@router.get("/search", response_model=List[FundResponse], summary="搜索基金")
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


@router.get("/followed/list", response_model=List[FollowedFundResponse], summary="获取自选基金列表")
async def get_followed_funds(
    current_user: User = Depends(get_current_user),
    service: FundFollowedQueryService = Depends(get_fund_followed_query_service),
) -> List[FollowedFundResponse]:
    """获取当前用户关注的所有基金及其最新行情。"""
    return await service.get_followed_funds(current_user.id)


@router.post("/follow", response_model=FollowedFundResponse, summary="关注基金")
async def follow_fund(
    fund_in: FollowedFundCreate,
    current_user: User = Depends(get_current_user),
    service: FundFollowCommandService = Depends(get_fund_follow_command_service),
) -> FollowedFundResponse:
    """将基金加入自选列表。"""
    try:
        return await service.follow_fund(
            user_id=current_user.id,
            fund_code=fund_in.fund_code,
            remark=fund_in.remark,
        )
    except FundNotFoundError as exc:
        raise HTTPException(status_code=404, detail="基金不存在") from exc


@router.delete("/unfollow/{code}", summary="取消关注基金")
async def unfollow_fund(
    code: str,
    current_user: User = Depends(get_current_user),
    service: FundFollowCommandService = Depends(get_fund_follow_command_service),
) -> dict:
    """从自选列表中移除基金。"""
    success = await service.unfollow_fund(current_user.id, code)
    if not success:
        raise HTTPException(status_code=404, detail="关注记录不存在")
    return {"message": "ok"}


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
        return await service.get(code, period)
    except FundPerformanceTrendNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Fund not found") from exc
    except FundPerformanceTrendUnsupportedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ValueError, FundPerformanceTrendUnavailableError) as exc:
        status_code = 400 if isinstance(exc, ValueError) else 503
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{code}", response_model=FundResponse, summary="获取基金详情")
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
