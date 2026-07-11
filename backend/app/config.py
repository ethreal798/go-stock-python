"""应用配置模块，使用 pydantic-settings 管理所有配置项。"""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，支持从环境变量和 .env 文件加载。

    重要：所有敏感配置（数据库连接、密钥等）都应该通过环境变量设置，
         不要依赖默认值，确保生产环境安全。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 应用基本配置 ----
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_NAME: str = "python-stock"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # ---- 安全与认证配置 ----
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 默认 7 天

    # ---- 数据库配置 ----
    # 默认使用 SQLite 作为开发环境，生产环境必须通过环境变量设置
    DATABASE_URL: str = "sqlite+aiosqlite:///./go_stock.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ---- Redis 配置 ----
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # ---- AI 模型配置 ----
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL_NAME: str = "gpt-4o"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 4096

    # ---- 备用 AI 模型配置（Ollama / DeepSeek 等） ----
    AI_OLLAMA_BASE_URL: str = "http://localhost:11434"
    AI_OLLAMA_MODEL: str = "qwen2.5:7b"
    AI_DEEPSEEK_API_KEY: str = ""
    AI_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    AI_DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---- CORS 配置 ----
    # 从环境变量读取，格式：http://localhost:5173,http://localhost:3000
    CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    # ---- 定时任务配置 ----
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"

    # ---- 数据源配置 ----
    EASTMONEY_API_BASE: str = "https://push2.eastmoney.com"
    SINA_API_BASE: str = "https://hq.sinajs.cn"
    TUSHARE_API_BASE: str = "https://api.tushare.pro"
    TUSHARE_TOKEN: str = ""

    def validate_required_settings(self) -> None:
        """验证必需的配置项，在生产环境必须设置。"""
        if not self.DEBUG:
            if not self.SECRET_KEY:
                raise ValueError("在非 DEBUG 模式下，SECRET_KEY 环境变量必须设置")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("在非 DEBUG 模式下，不建议使用 SQLite，请设置 DATABASE_URL 环境变量")


settings = Settings()

# 仅在生产环境验证必需配置
if not settings.DEBUG:
    settings.validate_required_settings()
