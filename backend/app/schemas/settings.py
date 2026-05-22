"""应用设置相关 Pydantic Schema。"""

from typing import Optional

from pydantic import BaseModel, Field


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
