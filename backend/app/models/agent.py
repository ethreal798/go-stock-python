"""LangGraph Agent 会话、运行任务和业务消息的持久化模型。"""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    """Agent 提示词模板。"""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), index=True)
    content = Column(Text)
    type = Column(String(50), index=True)


class AgentThread(Base, TimestampMixin):
    """用户会话，同时作为 LangGraph Checkpoint 的 thread_id。"""

    __tablename__ = "agent_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, index=True, nullable=False)
    title = Column(String(200), nullable=False, default="New conversation")
    capability = Column(String(50), index=True, nullable=False, default="general")
    model_config_id = Column(BigInteger, ForeignKey("user_ai_model_configs.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active", server_default="active")
    message_count = Column(Integer, nullable=False, default=0, server_default="0")
    total_input_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    total_output_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    last_message_at = Column(DateTime, nullable=True, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)

    runs = relationship("AgentRun", back_populates="thread", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", back_populates="thread", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_agent_threads_user_active_last", "user_id", "deleted_at", "last_message_at"),)


class AgentRun(Base, TimestampMixin):
    """一次可查询、可续传、可中断的后台模型执行任务。"""

    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(BigInteger, nullable=False, index=True)
    client_request_id = Column(String(64), nullable=False)
    user_message_id = Column(UUID(as_uuid=True), nullable=False)
    assistant_message_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    model_config_id = Column(BigInteger, ForeignKey("user_ai_model_configs.id"), nullable=False, index=True)
    capability = Column(String(50), nullable=False, default="general")
    status = Column(String(30), nullable=False, default="pending", server_default="pending", index=True)
    content_snapshot = Column(Text, nullable=False, default="", server_default="")
    last_event_id = Column(String(64), nullable=True)
    worker_id = Column(String(100), nullable=True, index=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    finish_reason = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    thread = relationship("AgentThread", back_populates="runs")
    messages = relationship("AgentMessage", back_populates="run")

    __table_args__ = (
        # 客户端重试只能命中同一个 Run，避免重复调用模型和重复计费。
        UniqueConstraint("user_id", "client_request_id", name="uq_agent_runs_user_client_request"),
        # 同一会话同一时刻只允许存在一个活动 Run。
        Index(
            "uq_agent_runs_active_thread",
            "thread_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running', 'cancel_requested')"),
        ),
        Index("ix_agent_runs_pending_created", "status", "created_at"),
    )


class AgentMessage(Base, TimestampMixin):
    """面向业务查询的消息投影，与 LangGraph Checkpoint 分开存储。"""

    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False, default="", server_default="")
    sequence = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="completed", server_default="completed")
    model_config_id = Column(BigInteger, ForeignKey("user_ai_model_configs.id"), nullable=True)
    model_name = Column(String(100), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    finish_reason = Column(String(50), nullable=True)
    tool_calls = Column(JSON, nullable=True)
    tool_call_id = Column(String(100), nullable=True)
    citations = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    visible = Column(Boolean, nullable=False, default=True, server_default="true")

    thread = relationship("AgentThread", back_populates="messages")
    run = relationship("AgentRun", back_populates="messages")

    __table_args__ = (
        UniqueConstraint("thread_id", "sequence", name="uq_agent_messages_thread_sequence"),
        Index("ix_agent_messages_thread_created", "thread_id", "created_at"),
    )
