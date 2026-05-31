"""应用配置模块，使用 pydantic-settings 管理所有配置项。"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，支持从环境变量和 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- 应用基本配置 ----
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_NAME: str = "python-stock"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # ---- 安全与认证配置 ----
    SECRET_KEY: str = "your-secret-key-here-please-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 默认 7 天

    # ---- 数据库配置 ----
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5432/py_stock"
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
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ---- 定时任务配置 ----
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"

    # ---- 数据源配置 ----
    EASTMONEY_API_BASE: str = "https://push2.eastmoney.com"
    SINA_API_BASE: str = "https://hq.sinajs.cn"
    TUSHARE_API_BASE: str = "https://api.tushare.pro"
    TUSHARE_TOKEN: str = ""


settings = Settings()
