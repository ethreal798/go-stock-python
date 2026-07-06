"""基金相关路由。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.fund import FundResponse, FollowedFundResponse, FollowedFundCreate
from app.services.fund_service import FundService
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


def get_fund_service(db: AsyncSession = Depends(get_db)) -> FundService:
    return FundService(db)


@router.get("/", response_model=List[FundResponse], summary="获取基金列表")
async def get_funds(
    keyword: Optional[str] = Query(None, description="搜索关键词(代码/名称)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    service: FundService = Depends(get_fund_service),
) -> List[FundResponse]:
    """获取全量基金列表，支持模糊搜索。"""
    return await service.get_funds(keyword=keyword, page=page, limit=limit)


# ============================================================
# 自选基金相关
# ============================================================


@router.get("/followed/list", response_model=List[FollowedFundResponse], summary="获取自选基金列表")
async def get_followed_funds(
    current_user: User = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
) -> List[FollowedFundResponse]:
    """获取当前用户关注的所有基金及其最新行情。"""
    return await service.get_followed_funds(current_user.id)


@router.post("/follow", response_model=FollowedFundResponse, summary="关注基金")
async def follow_fund(
    fund_in: FollowedFundCreate,
    current_user: User = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
) -> FollowedFundResponse:
    """将基金加入自选列表。"""
    return await service.follow_fund(user_id=current_user.id, fund_code=fund_in.fund_code, remark=fund_in.remark)


@router.delete("/follow/{code}", summary="取消关注基金")
async def unfollow_fund(
    code: str,
    current_user: User = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
) -> dict:
    """从自选列表中移除基金。"""
    success = await service.unfollow_fund(current_user.id, code)
    if not success:
        raise HTTPException(status_code=404, detail="关注记录不存在")
    return {"message": "Successfully unfollowed"}


@router.get("/{code}", response_model=FundResponse, summary="获取基金详情")
async def get_fund_detail(
    code: str,
    service: FundService = Depends(get_fund_service),
) -> FundResponse:
    """获取指定基金的详细信息，如果数据过旧会自动触发刷新。"""
    fund = await service.get_fund_detail(code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund


@router.post("/sync", summary="同步基金基础信息")
async def sync_funds(
    service: FundService = Depends(get_fund_service),
) -> dict:
    """手动触发同步全量基金基础信息（耗时操作）。"""
    count = await service.sync_all_fund_basics()
    return {"message": f"Successfully synced {count} funds"}
