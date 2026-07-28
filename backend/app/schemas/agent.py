"""Pydantic schemas for AI chat and agent endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request from the frontend."""

    message: str = Field(..., min_length=1, description="User message")
    model_config_id: int = Field(..., description="Selected user AI model config ID")
    conversation_id: str | None = Field(None, description="Existing conversation ID, empty means create one")
    capability: str | None = Field("general", description="Requested entry capability")


class ChatModelOption(BaseModel):
    """Enabled model config option shown on the chat page."""

    model_config_id: int = Field(..., description="User AI model config ID")
    name: str = Field(..., description="User-defined config name")
    provider: str = Field(..., description="Provider code")
    base_url: str = Field(..., description="OpenAI-compatible base URL")
    model_name: str = Field(..., description="Model name passed to the provider")
    api_key_configured: bool = Field(..., description="Whether this config has an API key")
    max_output_tokens: int = Field(..., description="Max output tokens")
    temperature: float = Field(..., description="Temperature")


class ChatMessage(BaseModel):
    """Single chat message returned to the frontend."""

    message_id: str | None = None
    role: str = Field(..., description="system / user / assistant / tool")
    content: str = Field(..., description="Message content")
    status: str = Field("completed", description="pending / streaming / completed / failed / canceled")
    capability: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    execution_engine: str | None = None
    model_config_id: int | None = None
    model_name: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None


class ChatStreamEvent(BaseModel):
    """SSE event payload shape used by stream_service."""

    event: str = Field(..., description="metadata / delta / tool_call / citations / usage / done / aborted / error")
    data: dict[str, Any] = Field(default_factory=dict)


class ChatHistoryResponse(BaseModel):
    """Chat history response."""

    conversation_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConversationSummary(BaseModel):
    """Conversation list item."""

    conversation_id: str
    title: str = ""
    capability: str | None = None
    execution_engine: str | None = None
    model_config_id: int | None = None
    model_name: str | None = None
    message_count: int = 0
    last_message_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
