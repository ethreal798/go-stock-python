"""add agent tables

Revision ID: c4f8a2b7d901
Revises: 8a1f4c2e7b90
Create Date: 2026-07-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c4f8a2b7d901"
down_revision: Union[str, None] = "8a1f4c2e7b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("capability", sa.String(length=50), nullable=False),
        sa.Column("model_config_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_config_id"], ["user_ai_model_configs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_threads_user_id", "agent_threads", ["user_id"])
    op.create_index("ix_agent_threads_capability", "agent_threads", ["capability"])
    op.create_index("ix_agent_threads_model_config_id", "agent_threads", ["model_config_id"])
    op.create_index("ix_agent_threads_last_message_at", "agent_threads", ["last_message_at"])
    op.create_index("ix_agent_threads_deleted_at", "agent_threads", ["deleted_at"])
    op.create_index("ix_agent_threads_user_active_last", "agent_threads", ["user_id", "deleted_at", "last_message_at"])

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("client_request_id", sa.String(length=64), nullable=False),
        sa.Column("user_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assistant_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_config_id", sa.BigInteger(), nullable=False),
        sa.Column("capability", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("content_snapshot", sa.Text(), server_default="", nullable=False),
        sa.Column("last_event_id", sa.String(length=64), nullable=True),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(length=50), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_config_id"], ["user_ai_model_configs.id"]),
        sa.ForeignKeyConstraint(["thread_id"], ["agent_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assistant_message_id"),
        sa.UniqueConstraint("user_id", "client_request_id", name="uq_agent_runs_user_client_request"),
    )
    op.create_index("ix_agent_runs_thread_id", "agent_runs", ["thread_id"])
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_model_config_id", "agent_runs", ["model_config_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_worker_id", "agent_runs", ["worker_id"])
    op.create_index("ix_agent_runs_lease_expires_at", "agent_runs", ["lease_expires_at"])
    op.create_index("ix_agent_runs_pending_created", "agent_runs", ["status", "created_at"])
    op.create_index(
        "uq_agent_runs_active_thread",
        "agent_runs",
        ["thread_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running', 'cancel_requested')"),
    )

    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="completed", nullable=False),
        sa.Column("model_config_id", sa.BigInteger(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(length=50), nullable=True),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_call_id", sa.String(length=100), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("visible", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_config_id"], ["user_ai_model_configs.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["thread_id"], ["agent_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "sequence", name="uq_agent_messages_thread_sequence"),
    )
    op.create_index("ix_agent_messages_thread_id", "agent_messages", ["thread_id"])
    op.create_index("ix_agent_messages_run_id", "agent_messages", ["run_id"])
    op.create_index("ix_agent_messages_thread_created", "agent_messages", ["thread_id", "created_at"])


def downgrade() -> None:
    op.drop_table("agent_messages")
    op.drop_table("agent_runs")
    op.drop_table("agent_threads")
