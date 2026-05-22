"""AI Agent 相关 Pydantic Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求。"""

    message: str = Field(..., description="用户消息", min_length=1)
    conversation_id: Optional[str] = Field(None, description="会话ID，为空则新建会话")
    model: Optional[str] = Field(None, description="指定使用的模型名称")
    stream: bool = Field(True, description="是否流式返回")


class ChatMessage(BaseModel):
    """单条聊天消息。"""

    role: str = Field(..., description="角色: user / assistant / system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = None
    tool_calls: Optional[list[dict]] = Field(None, description="工具调用信息")


class ChatResponse(BaseModel):
    """聊天响应（非流式）。"""

    conversation_id: str = Field(..., description="会话ID")
    message: ChatMessage = Field(..., description="助手回复消息")
    usage: Optional[dict] = Field(None, description="Token 用量统计")


class ChatHistoryResponse(BaseModel):
    """聊天历史响应。"""

    conversation_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationSummary(BaseModel):
    """会话摘要。"""

    conversation_id: str
    title: str = Field("", description="会话标题")
    message_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
