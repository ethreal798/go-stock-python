"""AI 相关模型"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from .base import Base, GormBaseModel, TimestampMixin


class AIResponseResult(GormBaseModel):
    """AI 响应结果"""

    __tablename__ = "ai_response_result"

    chat_id = Column(String(100), name="chat_id")
    model_name = Column(String(100), name="model_name")
    stock_code = Column(String(20), name="stock_code")
    stock_name = Column(String(50), name="stock_name")
    question = Column(Text)
    content = Column(Text)
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")


class AIRecommendStocks(GormBaseModel):
    """AI 推荐股票"""

    __tablename__ = "ai_recommend_stocks"

    data_time = Column(DateTime, index=True, name="data_time")
    model_name = Column(String(100), name="model_name")
    rating = Column(String(20))
    stock_code = Column(String(20), name="stock_code")
    stock_name = Column(String(50), name="stock_name")
    bk_code = Column(String(50), name="bk_code")
    bk_name = Column(String(100), name="bk_name")
    stock_price = Column(String(20), name="stock_price")
    stock_current_price = Column(String(20), name="stock_current_price")
    stock_current_price_time = Column(String(50), name="stock_current_price_time")
    stock_close_price = Column(String(20), name="stock_close_price")
    stock_pre_price = Column(String(20), name="stock_pre_price")
    recommend_reason = Column(Text, name="recommend_reason")
    recommend_buy_price = Column(String(50), name="recommend_buy_price")
    recommend_buy_price_min = Column(Float, name="recommend_buy_price_min")
    recommend_buy_price_max = Column(Float, name="recommend_buy_price_max")
    recommend_stop_profit_price = Column(String(50), name="recommend_stop_profit_price")
    recommend_stop_profit_price_min = Column(Float, name="recommend_stop_profit_price_min")
    recommend_stop_profit_price_max = Column(Float, name="recommend_stop_profit_price_max")
    recommend_stop_loss_price = Column(String(50), name="recommend_stop_loss_price")
    risk_remarks = Column(Text, name="risk_remarks")
    remarks = Column(Text)
    enable_alert = Column(Boolean, default=False, server_default="0", name="enable_alert")


class PromptTemplate(Base, TimestampMixin):
    """提示词模板"""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    content = Column(Text)
    type = Column(String(50))


class ChatMemory(Base):
    """聊天记忆"""

    __tablename__ = "chat_memory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, name="session_id")
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now(), name="created_at")


class ChatConversation(GormBaseModel):
    """AI chat conversation metadata."""

    __tablename__ = "chat_conversations"

    conversation_id = Column(String(64), unique=True, index=True, nullable=False, comment="Public conversation UUID")
    user_id = Column(BigInteger, index=True, nullable=False, comment="Owner user ID")
    title = Column(String(200), nullable=True, comment="Conversation title")
    capability = Column(String(50), index=True, nullable=False, default="general", comment="Primary capability")
    execution_engine = Column(String(30), nullable=False, default="llm", comment="Execution engine")
    rag_enabled = Column(
        Boolean, nullable=False, default=False, server_default="false", comment="Whether RAG is enabled"
    )
    tool_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether tool calling is enabled",
    )
    model_config_id = Column(
        BigInteger,
        ForeignKey("user_ai_model_configs.id"),
        index=True,
        nullable=False,
        comment="User AI model config ID",
    )
    model_name = Column(String(100), nullable=True, comment="Last actual model name")
    agent_config_id = Column(BigInteger, nullable=True, comment="Reserved agent or graph config ID")
    message_count = Column(Integer, nullable=False, default=0, server_default="0", comment="Message count")
    total_input_tokens = Column(Integer, nullable=False, default=0, server_default="0", comment="Input token total")
    total_output_tokens = Column(Integer, nullable=False, default=0, server_default="0", comment="Output token total")
    total_tokens = Column(Integer, nullable=False, default=0, server_default="0", comment="Token total")
    last_message_at = Column(DateTime, index=True, nullable=True, comment="Last message time")
    extra_metadata = Column(JSON, nullable=True, comment="Extension metadata")

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_chat_conversations_user_deleted_last", "user_id", "deleted_at", "last_message_at"),)


class ChatMessage(Base, TimestampMixin):
    """AI chat message detail."""

    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(String(64), unique=True, index=True, nullable=False, comment="Public message UUID")
    conversation_db_id = Column(
        BigInteger,
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="Conversation database ID",
    )
    role = Column(String(20), nullable=False, comment="system/user/assistant/tool")
    content = Column(Text, nullable=False, comment="Message content")
    message_index = Column(Integer, nullable=False, comment="Message order in conversation")
    capability = Column(String(50), index=True, nullable=True, comment="Primary capability used by this turn")
    capabilities = Column(JSON, nullable=True, comment="Capability set used by this turn")
    execution_engine = Column(String(30), nullable=True, comment="Execution engine used by this turn")
    rag_enabled = Column(
        Boolean, nullable=False, default=False, server_default="false", comment="Whether RAG was enabled"
    )
    tool_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether tool calling was enabled",
    )
    status = Column(
        String(20), nullable=False, default="completed", server_default="completed", comment="Message status"
    )
    model_config_id = Column(
        BigInteger,
        ForeignKey("user_ai_model_configs.id"),
        index=True,
        nullable=True,
        comment="User AI model config ID used by this turn",
    )
    model_name = Column(String(100), nullable=True, comment="Actual model name")
    input_tokens = Column(Integer, nullable=True, comment="Input tokens")
    output_tokens = Column(Integer, nullable=True, comment="Output tokens")
    total_tokens = Column(Integer, nullable=True, comment="Total tokens")
    finish_reason = Column(String(50), nullable=True, comment="LLM finish reason")
    tool_calls = Column(JSON, nullable=True, comment="Assistant tool call payloads")
    tool_call_id = Column(String(100), nullable=True, comment="Tool call ID for tool messages")
    citations = Column(JSON, nullable=True, comment="RAG citations")
    extra_metadata = Column(JSON, nullable=True, comment="Extension metadata")
    error_message = Column(Text, nullable=True, comment="Error message")

    conversation = relationship("ChatConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_chat_messages_conversation_index", "conversation_db_id", "message_index", unique=True),
        Index("ix_chat_messages_created_at", "created_at"),
    )
