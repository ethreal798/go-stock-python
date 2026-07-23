"""应用设置相关 Pydantic Schema。"""

from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AIModelConfig(BaseModel):
    """AI 模型配置。"""

    api_key: str = Field("", description="API Key")
    base_url: str = Field("https://api.openai.com/v1", description="API Base URL")
    model_name: str = Field("gpt-4o", description="模型名称")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(4096, ge=1, le=128000, description="最大 Token 数")


class AlertConfig(BaseModel):
    """预警配置。"""

    enabled: bool = Field(True, description="是否启用预警")
    price_alert: bool = Field(True, description="价格预警")
    volume_alert: bool = Field(True, description="成交量预警")
    dingtalk_webhook: str = Field("", description="钉钉机器人 Webhook")


class DataSourceConfig(BaseModel):
    """数据源配置。"""

    eastmoney_enabled: bool = Field(True, description="启用东方财富数据源")
    sina_enabled: bool = Field(True, description="启用新浪数据源")
    tdx_enabled: bool = Field(True, description="启用通达信数据源")
    tushare_token: str = Field("", description="Tushare Token")


class SettingsUpdate(BaseModel):
    """设置更新请求。"""

    ai_config: Optional[AIModelConfig] = Field(None, description="AI 模型配置")
    alert_config: Optional[AlertConfig] = Field(None, description="预警配置")
    data_source_config: Optional[DataSourceConfig] = Field(None, description="数据源配置")


class SettingsResponse(BaseModel):
    """设置响应。"""

    ai_config: AIModelConfig = Field(default_factory=AIModelConfig)
    alert_config: AlertConfig = Field(default_factory=AlertConfig)
    data_source_config: DataSourceConfig = Field(default_factory=DataSourceConfig)


class UserAIModelConfigBase(BaseModel):
    """用户级 AI 模型配置基础字段。"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    provider: str = Field("openai_compatible", min_length=1, max_length=50, description="供应商标识")
    base_url: str = Field("https://api.openai.com/v1", min_length=1, max_length=500, description="API Base URL")
    model: str = Field("gpt-4o-mini", min_length=1, max_length=100, description="模型名称")
    max_output_tokens: int = Field(4096, ge=1, le=128000, description="最大输出 Token 数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    timeout_seconds: int = Field(60, ge=1, le=300, description="请求超时时间")
    enabled: bool = Field(True, description="是否启用")
    extra_config: dict[str, Any] = Field(default_factory=dict, description="扩展配置")

    @field_validator("name", "provider", "base_url", "model", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class UserAIModelConfigCreate(UserAIModelConfigBase):
    """创建用户级 AI 模型配置请求。"""

    api_key: Optional[str] = Field(None, min_length=1, max_length=4096, description="API Key，只写不回显")

    @field_validator("api_key", mode="before")
    @classmethod
    def strip_api_key(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class UserAIModelConfigUpdate(BaseModel):
    """更新用户级 AI 模型配置请求。"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称")
    provider: Optional[str] = Field(None, min_length=1, max_length=50, description="供应商标识")
    base_url: Optional[str] = Field(None, min_length=1, max_length=500, description="API Base URL")
    model: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    api_key: Optional[str] = Field(None, min_length=1, max_length=4096, description="API Key，只写不回显")
    clear_api_key: bool = Field(False, description="是否明确清除已保存 API Key")
    max_output_tokens: Optional[int] = Field(None, ge=1, le=128000, description="最大输出 Token 数")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300, description="请求超时时间")
    enabled: Optional[bool] = Field(None, description="是否启用")
    extra_config: Optional[dict[str, Any]] = Field(None, description="扩展配置")

    @field_validator("name", "provider", "base_url", "model", "api_key", mode="before")
    @classmethod
    def strip_optional_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_api_key_operation(self) -> "UserAIModelConfigUpdate":
        if self.api_key is not None and self.clear_api_key:
            raise ValueError("api_key 与 clear_api_key 不能同时使用")
        return self


class UserAIModelConfigResponse(BaseModel):
    """用户级 AI 模型配置响应。"""

    id: int
    name: str
    provider: str
    base_url: str
    model: str
    api_key_configured: bool
    api_key_hint: Optional[str] = None
    max_output_tokens: int
    temperature: float
    timeout_seconds: int
    enabled: bool
    extra_config: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SavedAIModelConfigTestRequest(BaseModel):
    """已保存模型配置连接测试请求。"""

    message: str = Field("ping", min_length=1, max_length=2000, description="测试消息")

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class InlineAIModelConfigTestRequest(UserAIModelConfigBase):
    """未保存模型配置连接测试请求。"""

    api_key: Optional[str] = Field(None, min_length=1, max_length=4096, description="API Key，只用于本次测试")
    message: str = Field("ping", min_length=1, max_length=2000, description="测试消息")

    @field_validator("api_key", "message", mode="before")
    @classmethod
    def strip_inline_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class AIModelConfigTestResponse(BaseModel):
    """模型配置连接测试响应。"""

    success: bool
    message: str
    latency_ms: Optional[int] = None
    model: Optional[str] = None
    usage: Optional[dict[str, Any]] = None
