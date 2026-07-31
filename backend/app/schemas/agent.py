"""LangGraph Agent 的会话、运行任务和消息接口模型。"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentThreadCreate(BaseModel):
    """创建 Agent 会话的请求参数。"""

    model_config = ConfigDict(title="创建 Agent 会话请求")

    title: str | None = Field(None, max_length=200, description="会话标题；不传时使用默认标题")
    model_config_id: int = Field(..., description="当前用户的 AI 模型配置 ID")
    capability: str = Field("general", description="Agent 能力代码，当前支持 general")


class AgentThreadResponse(BaseModel):
    """Agent 会话信息。"""

    model_config = ConfigDict(title="Agent 会话")

    thread_id: UUID = Field(..., description="会话 ID，同时作为 LangGraph checkpoint thread_id")
    title: str = Field(..., description="会话标题")
    capability: str = Field(..., description="会话当前使用的能力代码")
    model_config_id: int = Field(..., description="会话当前使用的 AI 模型配置 ID")
    status: str = Field(..., description="会话状态")
    message_count: int = Field(..., description="会话中的消息总数")
    last_message_at: datetime | None = Field(None, description="最后一条消息的时间")
    created_at: datetime | None = Field(None, description="会话创建时间")


class AgentThreadDeleteResponse(BaseModel):
    """删除 Agent 会话后的响应。"""

    model_config = ConfigDict(title="删除 Agent 会话响应")

    thread_id: UUID = Field(..., description="已删除的会话 ID")
    deleted: bool = Field(True, description="是否已完成软删除")
    active_run_id: UUID | None = Field(None, description="删除时存在的活动任务 ID")
    run_status: str | None = Field(None, description="活动任务删除后的状态")


class AgentModelOption(BaseModel):
    """当前用户可用于 Agent 对话的模型选项。"""

    model_config = ConfigDict(title="Agent 可用模型")

    model_config_id: int = Field(..., description="用户 AI 模型配置 ID")
    name: str = Field(..., description="用户定义的配置名称")
    provider: str = Field(..., description="模型供应商标识")
    base_url: str = Field(..., description="OpenAI-compatible 接口地址")
    model_name: str = Field(..., description="提交给模型服务的模型名称")
    api_key_configured: bool = Field(..., description="是否已经配置 API Key")
    max_output_tokens: int = Field(..., description="最大输出 Token 数")
    temperature: float = Field(..., description="模型温度参数")


class AgentRunCreate(BaseModel):
    """在指定会话中创建运行任务的基础参数。"""

    model_config = ConfigDict(title="创建 Agent 运行任务请求")

    message: str = Field(..., min_length=1, description="用户本次发送的消息")
    model_config_id: int = Field(..., description="当前用户的 AI 模型配置 ID")
    capability: str = Field("general", description="本次运行使用的 Agent 能力代码")
    client_request_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="客户端幂等请求 ID；同一次重试必须使用相同值",
    )


class AgentRunSubmit(AgentRunCreate):
    """提交消息并按需创建会话的聚合请求。"""

    model_config = ConfigDict(title="提交 Agent 消息请求")

    thread_id: UUID | None = Field(None, description="已有会话 ID；为空时由后端自动创建会话")


class AgentRunResponse(BaseModel):
    """后台运行任务的状态与持久化快照。"""

    model_config = ConfigDict(title="Agent 运行任务")

    run_id: UUID = Field(..., description="本次模型生成任务 ID")
    thread_id: UUID = Field(..., description="任务所属的会话 ID")
    user_message_id: UUID = Field(..., description="本次用户消息 ID")
    assistant_message_id: UUID = Field(..., description="本次助手回复消息 ID")
    status: str = Field(
        ...,
        description="任务状态：pending、running、cancel_requested、completed、canceled、failed 或 interrupted",
    )
    content: str = Field("", description="已持久化的助手回复内容快照")
    last_event_id: str | None = Field(None, description="最近写入的 Redis Stream 事件 ID")
    model_name: str | None = Field(None, description="实际调用的模型名称")
    usage: dict[str, int | None] | None = Field(None, description="模型 Token 用量")
    error_message: str | None = Field(None, description="任务失败或中断时的错误信息")
    created_at: datetime | None = Field(None, description="任务创建时间")
    started_at: datetime | None = Field(None, description="Worker 开始执行时间")
    finished_at: datetime | None = Field(None, description="任务结束时间")


class AgentRunSubmitResponse(AgentRunResponse):
    """提交任务后的响应，包含可直接订阅的 SSE 地址。"""

    model_config = ConfigDict(title="提交 Agent 消息响应")

    stream_url: str = Field(..., description="本次运行任务的 SSE 订阅地址")


class AgentMessageResponse(BaseModel):
    """会话中的一条业务消息。"""

    model_config = ConfigDict(title="Agent 消息")

    message_id: UUID = Field(..., description="消息 ID")
    run_id: UUID | None = Field(None, description="产生该消息的运行任务 ID")
    role: str = Field(..., description="消息角色：user、assistant、system 或 tool")
    content: str = Field(..., description="消息正文")
    sequence: int = Field(..., description="消息在会话中的顺序号")
    status: str = Field(..., description="消息状态")
    model_config_id: int | None = Field(None, description="消息使用的 AI 模型配置 ID")
    model_name: str | None = Field(None, description="消息实际使用的模型名称")
    citations: list[dict[str, Any]] = Field(default_factory=list, description="RAG 引用来源")
    tool_calls: list[dict[str, Any]] = Field(default_factory=list, description="工具调用记录")
    created_at: datetime | None = Field(None, description="消息创建时间")


class AgentRunAbortResponse(BaseModel):
    """请求中断运行任务后的响应。"""

    model_config = ConfigDict(title="中断 Agent 任务响应")

    run_id: UUID = Field(..., description="运行任务 ID")
    status: str = Field(..., description="任务当前状态")
