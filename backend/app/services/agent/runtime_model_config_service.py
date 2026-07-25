"""Resolve user model configs into runtime-safe LLM configuration."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


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

    async def resolve(self, user_id: int, model_config_id: int) -> RuntimeModelConfig:
        """Resolve model_config_id owned by user_id.

        TODO: Reuse AIModelConfigService's validation/decryption path or move that
        shared logic into a common helper.
        """
        raise NotImplementedError
