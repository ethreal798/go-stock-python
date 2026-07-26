"""Resolve user model configs into runtime-safe LLM configuration."""

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import UserAIModelConfig
from app.schemas.agent import ChatModelOption
from app.services.ai_model_config_secret_service import AIModelConfigSecretService


@dataclass(frozen=True)
class RuntimeModelConfig:
    """Decrypted model configuration used at request time."""

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
    """Load and validate a user's selected model config for chat runtime."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.secret_service = AIModelConfigSecretService()

    async def resolve(self, user_id: int, model_config_id: int) -> RuntimeModelConfig:
        """Resolve an enabled model config owned by user_id for chat runtime."""
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

    async def list_chat_model_options(self, user_id: int) -> list[ChatModelOption]:
        """Return enabled model configs available on the chat page."""
        stmt = (
            select(UserAIModelConfig)
            .where(
                UserAIModelConfig.user_id == user_id,
                UserAIModelConfig.enabled.is_(True),
                UserAIModelConfig.deleted_at.is_(None),
            )
            .order_by(desc(UserAIModelConfig.updated_at), desc(UserAIModelConfig.id))
        )
        result = await self.db.execute(stmt)
        return [self._to_chat_model_option(config) for config in result.scalars().all()]

    @staticmethod
    def _to_chat_model_option(config: UserAIModelConfig) -> ChatModelOption:
        return ChatModelOption(
            model_config_id=config.id,
            name=config.name,
            provider=config.provider,
            base_url=config.base_url,
            model_name=config.model,
            api_key_configured=bool(config.api_key_ciphertext),
            max_output_tokens=config.max_output_tokens,
            temperature=config.temperature,
        )
