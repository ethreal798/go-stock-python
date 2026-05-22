"""应用设置路由。"""

from fastapi import APIRouter

from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

# 内存中的临时设置（后续迁移到数据库）
_current_settings = SettingsResponse()


@router.get("", response_model=SettingsResponse, summary="获取设置")
async def get_settings() -> SettingsResponse:
    """获取当前应用设置。"""
    # TODO: 从数据库/Redis 读取持久化设置
    return _current_settings


@router.put("", response_model=SettingsResponse, summary="更新设置")
async def update_settings(update: SettingsUpdate) -> SettingsResponse:
    """更新应用设置。"""
    global _current_settings

    if update.ai_config is not None:
        _current_settings.ai_config = update.ai_config
    if update.alert_config is not None:
        _current_settings.alert_config = update.alert_config
    if update.data_source_config is not None:
        _current_settings.data_source_config = update.data_source_config

    # TODO: 持久化到数据库/Redis
    return _current_settings
