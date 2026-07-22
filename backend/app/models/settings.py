"""User-level settings models."""

from sqlalchemy import JSON, BigInteger, Boolean, Column, Float, Index, Integer, String, Text, text

from .base import GormBaseModel


class UserAIModelConfig(GormBaseModel):
    """AI model configuration owned by one user."""

    __tablename__ = "user_ai_model_configs"
    __table_args__ = (
        Index(
            "uq_user_ai_model_configs_user_name_active",
            "user_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_user_ai_model_configs_user_default_active",
            "user_id",
            unique=True,
            postgresql_where=text("is_default = true AND deleted_at IS NULL"),
        ),
    )

    user_id = Column(BigInteger, index=True, nullable=False, comment="用户ID")
    name = Column(String(100), nullable=False, comment="配置名称")
    provider = Column(String(50), nullable=False, default="openai_compatible", comment="供应商标识")
    base_url = Column(String(500), nullable=False, comment="OpenAI兼容接口Base URL")
    model = Column(String(100), nullable=False, comment="模型名称")
    api_key_ciphertext = Column(Text, nullable=True, comment="加密后的API Key")
    api_key_hint = Column(String(32), nullable=True, comment="API Key脱敏提示")
    max_output_tokens = Column(Integer, nullable=False, default=4096, comment="最大输出Token数")
    temperature = Column(Float, nullable=False, default=0.7, comment="温度参数")
    timeout_seconds = Column(Integer, nullable=False, default=60, comment="请求超时时间")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认配置")
    extra_config = Column(JSON, nullable=True, comment="扩展配置")
