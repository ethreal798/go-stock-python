"""User AI model configuration service."""

import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.url_safety import BaseURLSafetyError, validate_ai_base_url
from app.models.settings import UserAIModelConfig
from app.schemas.settings import (
    AIModelConfigTestResponse,
    InlineAIModelConfigTestRequest,
    UserAIModelConfigCreate,
    UserAIModelConfigResponse,
    UserAIModelConfigUpdate,
)
from app.services.ai_model_config_secret_service import AIModelConfigSecretService


class AIModelConfigService:
    """Manage per-user OpenAI-compatible model configurations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.secret_service = AIModelConfigSecretService()

    async def list_configs(self, user_id: int) -> list[UserAIModelConfigResponse]:
        stmt = (
            select(UserAIModelConfig)
            .where(UserAIModelConfig.user_id == user_id, UserAIModelConfig.deleted_at.is_(None))
            .order_by(desc(UserAIModelConfig.enabled), desc(UserAIModelConfig.updated_at), desc(UserAIModelConfig.id))
        )
        result = await self.db.execute(stmt)
        return [self._to_response(config) for config in result.scalars().all()]

    async def get_config(self, user_id: int, config_id: int) -> UserAIModelConfigResponse:
        config = await self._get_config_model(user_id, config_id)
        return self._to_response(config)

    async def create_config(self, user_id: int, config_in: UserAIModelConfigCreate) -> UserAIModelConfigResponse:
        await self._ensure_name_available(user_id=user_id, name=config_in.name)
        await self._ensure_model_available(user_id=user_id, model=config_in.model)
        base_url = await self._validate_base_url(config_in.base_url)

        config = UserAIModelConfig(
            user_id=user_id,
            name=config_in.name,
            provider=config_in.provider,
            base_url=base_url,
            model=config_in.model,
            max_output_tokens=config_in.max_output_tokens,
            temperature=config_in.temperature,
            timeout_seconds=config_in.timeout_seconds,
            enabled=config_in.enabled,
            extra_config=config_in.extra_config or {},
        )

        self.db.add(config)
        await self.db.flush()

        if config_in.api_key:
            config.api_key_ciphertext, config.api_key_hint = self.secret_service.encrypt_api_key(
                user_id,
                config.id,
                config_in.api_key,
            )

        await self._commit_or_conflict()
        await self.db.refresh(config)
        return self._to_response(config)

    async def update_config(
        self,
        user_id: int,
        config_id: int,
        config_in: UserAIModelConfigUpdate,
    ) -> UserAIModelConfigResponse:
        config = await self._get_config_model(user_id, config_id)

        if config_in.name is not None and config_in.name != config.name:
            await self._ensure_name_available(user_id=user_id, name=config_in.name, exclude_id=config.id)
        if config_in.model is not None and config_in.model != config.model:
            await self._ensure_model_available(user_id=user_id, model=config_in.model, exclude_id=config.id)

        if config_in.name is not None:
            config.name = config_in.name
        if config_in.provider is not None:
            config.provider = config_in.provider
        if config_in.base_url is not None:
            config.base_url = await self._validate_base_url(config_in.base_url)
        if config_in.model is not None:
            config.model = config_in.model
        if config_in.max_output_tokens is not None:
            config.max_output_tokens = config_in.max_output_tokens
        if config_in.temperature is not None:
            config.temperature = config_in.temperature
        if config_in.timeout_seconds is not None:
            config.timeout_seconds = config_in.timeout_seconds
        if config_in.enabled is not None:
            config.enabled = config_in.enabled
        if config_in.extra_config is not None:
            config.extra_config = config_in.extra_config

        if config_in.clear_api_key:
            config.api_key_ciphertext = None
            config.api_key_hint = None
        elif config_in.api_key is not None:
            config.api_key_ciphertext, config.api_key_hint = self.secret_service.encrypt_api_key(
                user_id,
                config.id,
                config_in.api_key,
            )

        await self._commit_or_conflict()
        await self.db.refresh(config)
        return self._to_response(config)

    async def delete_config(self, user_id: int, config_id: int) -> None:
        config = await self._get_config_model(user_id, config_id)
        config.deleted_at = datetime.now()
        await self.db.commit()

    async def test_saved_config(
        self,
        user_id: int,
        config_id: int,
        message: str,
    ) -> AIModelConfigTestResponse:
        config = await self._get_config_model(user_id, config_id)
        api_key = self.secret_service.decrypt_api_key(user_id, config)
        return await self._test_openai_compatible(
            base_url=config.base_url,
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            timeout_seconds=config.timeout_seconds,
            message=message,
        )

    async def test_inline_config(self, config_in: InlineAIModelConfigTestRequest) -> AIModelConfigTestResponse:
        return await self._test_openai_compatible(
            base_url=config_in.base_url,
            model=config_in.model,
            api_key=config_in.api_key,
            temperature=config_in.temperature,
            max_output_tokens=config_in.max_output_tokens,
            timeout_seconds=config_in.timeout_seconds,
            message=config_in.message,
        )

    async def _get_config_model(self, user_id: int, config_id: int) -> UserAIModelConfig:
        stmt = select(UserAIModelConfig).where(
            UserAIModelConfig.id == config_id,
            UserAIModelConfig.user_id == user_id,
            UserAIModelConfig.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")
        return config

    async def _ensure_name_available(self, user_id: int, name: str, exclude_id: int | None = None) -> None:
        stmt = select(UserAIModelConfig.id).where(
            UserAIModelConfig.user_id == user_id,
            UserAIModelConfig.name == name,
            UserAIModelConfig.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(UserAIModelConfig.id != exclude_id)

        result = await self.db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同名模型配置已存在")

    async def _ensure_model_available(self, user_id: int, model: str, exclude_id: int | None = None) -> None:
        stmt = select(UserAIModelConfig.id).where(
            UserAIModelConfig.user_id == user_id,
            UserAIModelConfig.model == model,
            UserAIModelConfig.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(UserAIModelConfig.id != exclude_id)

        result = await self.db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同名模型已存在")

    async def _validate_base_url(self, base_url: str) -> str:
        try:
            return await validate_ai_base_url(base_url, resolve_host=True)
        except BaseURLSafetyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def _commit_or_conflict(self) -> None:
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="模型配置保存冲突，请刷新后重试") from exc

    @staticmethod
    def _to_response(config: UserAIModelConfig) -> UserAIModelConfigResponse:
        return UserAIModelConfigResponse(
            id=config.id,
            name=config.name,
            provider=config.provider,
            base_url=config.base_url,
            model=config.model,
            api_key_configured=bool(config.api_key_ciphertext),
            api_key_hint=config.api_key_hint,
            max_output_tokens=config.max_output_tokens,
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
            enabled=config.enabled,
            extra_config=config.extra_config or {},
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    async def _test_openai_compatible(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
        temperature: float,
        max_output_tokens: int,
        timeout_seconds: int,
        message: str,
    ) -> AIModelConfigTestResponse:
        try:
            normalized_base_url = await validate_ai_base_url(base_url, resolve_host=True)
        except BaseURLSafetyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        url = f"{normalized_base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens": min(max_output_tokens, 16),
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        start_time = time.perf_counter()
        try:
            timeout = httpx.Timeout(float(timeout_seconds or settings.AI_MODEL_CONFIG_TEST_TIMEOUT_SECONDS))
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            return AIModelConfigTestResponse(success=False, message="连接测试超时")
        except httpx.ConnectError:
            return AIModelConfigTestResponse(success=False, message="无法连接到模型服务")
        except httpx.RequestError:
            return AIModelConfigTestResponse(success=False, message="连接测试失败")

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        if 200 <= response.status_code < 300:
            data = self._safe_json(response)
            return AIModelConfigTestResponse(
                success=True,
                message="连接测试成功",
                latency_ms=latency_ms,
                model=data.get("model") or model,
                usage=data.get("usage"),
            )

        return AIModelConfigTestResponse(
            success=False,
            message=self._provider_error_message(response.status_code),
            latency_ms=latency_ms,
            model=model,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}

    @staticmethod
    def _provider_error_message(status_code: int) -> str:
        if 300 <= status_code < 400:
            return "模型服务返回重定向，已被安全策略拒绝"
        if status_code in {401, 403}:
            return "API Key 认证失败或无访问权限"
        if status_code == 404:
            return "模型或接口地址不存在"
        if status_code == 429:
            return "模型服务限流，请稍后重试"
        if status_code >= 500:
            return "模型服务暂时不可用"
        return f"模型服务返回 HTTP {status_code}"
