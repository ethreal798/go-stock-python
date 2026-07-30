"""校验用户模型配置，并生成可安全用于运行时的模型参数。"""

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import UserAIModelConfig
from app.services.ai_model_config_secret_service import AIModelConfigSecretService


@dataclass(frozen=True)
class RuntimeModelConfig:
    """仅在 Worker 内存中短暂存在的已解密模型配置。"""

    id: int
    provider: str
    base_url: str
    model: str
    api_key: str | None
    temperature: float
    max_output_tokens: int
    timeout_seconds: int
    extra_config: dict[str, Any]


class RuntimeModelConfigService:
    """读取、鉴权并解密当前用户选择的模型配置。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.secret_service = AIModelConfigSecretService()

    async def resolve(self, user_id: int, model_config_id: int) -> RuntimeModelConfig:
        """返回用户拥有且未删除、未禁用的模型配置。"""
        stmt = select(UserAIModelConfig).where(
            UserAIModelConfig.id == model_config_id,
            UserAIModelConfig.user_id == user_id,
            UserAIModelConfig.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")
        if not config.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="模型配置已禁用")

        return RuntimeModelConfig(
            id=config.id,
            provider=config.provider,
            base_url=config.base_url,
            model=config.model,
            api_key=self.secret_service.decrypt_api_key(user_id, config),
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            timeout_seconds=config.timeout_seconds,
            extra_config=config.extra_config or {},
        )
