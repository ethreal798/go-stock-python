"""Shared encryption helpers for user AI model configs."""

from fastapi import HTTPException

from app.core.crypto import SecretCipher, SecretCipherError
from app.models.settings import UserAIModelConfig


class AIModelConfigSecretService:
    """Encrypt and decrypt API keys for user AI model configs."""

    def __init__(self) -> None:
        self._cipher: SecretCipher | None = None

    def encrypt_api_key(self, user_id: int, config_id: int, api_key: str) -> tuple[str, str | None]:
        """Encrypt an API key and return ciphertext plus display hint."""
        return self._cipher_instance.encrypt(api_key, self.aad(user_id, config_id)), SecretCipher.build_hint(api_key)

    def decrypt_api_key(self, user_id: int, config: UserAIModelConfig) -> str | None:
        """Decrypt a saved API key for runtime use."""
        if not config.api_key_ciphertext:
            return None

        try:
            return self._cipher_instance.decrypt(config.api_key_ciphertext, self.aad(user_id, config.id))
        except SecretCipherError as exc:
            raise HTTPException(status_code=500, detail="API Key 解密失败，请重新保存 API Key") from exc

    @staticmethod
    def aad(user_id: int, config_id: int) -> str:
        """Additional authenticated data bound to user and config IDs."""
        return f"user_ai_model_config:{user_id}:{config_id}"

    @property
    def _cipher_instance(self) -> SecretCipher:
        if self._cipher is None:
            self._cipher = SecretCipher()
        return self._cipher
