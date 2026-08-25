"""应用设置路由。"""

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import ApiResponse
from app.models.user import User
from app.routers.auth import get_user_service, oauth2_scheme
from app.schemas.settings import (
    AIModelConfigTestResponse,
    InlineAIModelConfigTestRequest,
    SavedAIModelConfigTestRequest,
    UserAIModelConfigCreate,
    UserAIModelConfigResponse,
    UserAIModelConfigUpdate,
)
from app.services.ai_model_config_service import AIModelConfigService
from app.services.user.user_service import UserService

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """获取当前登录用户。"""
    return await user_service.get_current_user(token)


def get_ai_model_config_service(db: AsyncSession = Depends(get_db)) -> AIModelConfigService:
    return AIModelConfigService(db)


@router.get("/ai-models", response_model=list[UserAIModelConfigResponse], summary="获取当前用户 AI 模型配置列表")
async def list_ai_model_configs(
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> list[UserAIModelConfigResponse]:
    """获取当前用户的所有 AI 模型配置。"""
    return await service.list_configs(current_user.id)


@router.post(
    "/ai-models",
    response_model=UserAIModelConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建当前用户 AI 模型配置",
)
async def create_ai_model_config(
    config_in: UserAIModelConfigCreate,
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> UserAIModelConfigResponse:
    """创建 AI 模型配置，API Key 加密保存且不会回显。"""
    return await service.create_config(current_user.id, config_in)


@router.post("/ai-models/test", response_model=AIModelConfigTestResponse, summary="测试未保存的 AI 模型配置")
async def test_inline_ai_model_config(
    config_in: InlineAIModelConfigTestRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> AIModelConfigTestResponse:
    """测试一组未保存的 OpenAI 兼容模型配置。"""
    _ = current_user
    return await service.test_inline_config(config_in)


@router.get("/ai-models/{config_id}", response_model=UserAIModelConfigResponse, summary="获取 AI 模型配置详情")
async def get_ai_model_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> UserAIModelConfigResponse:
    """获取当前用户的指定 AI 模型配置。"""
    return await service.get_config(current_user.id, config_id)


@router.patch("/ai-models/{config_id}", response_model=UserAIModelConfigResponse, summary="更新 AI 模型配置")
async def update_ai_model_config(
    config_id: int,
    config_in: UserAIModelConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> UserAIModelConfigResponse:
    """更新 AI 模型配置。未传 API Key 时保留原密钥。"""
    return await service.update_config(current_user.id, config_id, config_in)


@router.delete("/ai-models/{config_id}", summary="删除 AI 模型配置")
async def delete_ai_model_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> ApiResponse:
    """软删除 AI 模型配置。"""
    return ApiResponse.success(msg="操作成功", data=await service.delete_config(current_user.id, config_id))


@router.post(
    "/ai-models/{config_id}/test",
    response_model=AIModelConfigTestResponse,
    summary="测试已保存的 AI 模型配置",
)
async def test_saved_ai_model_config(
    config_id: int,
    request: SavedAIModelConfigTestRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> AIModelConfigTestResponse:
    """测试已保存配置的 OpenAI 兼容接口连通性。"""
    message = request.message if request is not None else "ping"
    return await service.test_saved_config(current_user.id, config_id, message)
