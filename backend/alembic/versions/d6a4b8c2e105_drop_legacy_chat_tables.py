"""drop legacy chat tables

Revision ID: d6a4b8c2e105
Revises: c4f8a2b7d901
Create Date: 2026-07-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d6a4b8c2e105"
down_revision: Union[str, None] = "c4f8a2b7d901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")


def downgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("capability", sa.String(length=50), nullable=False),
        sa.Column("execution_engine", sa.String(length=30), nullable=False),
        sa.Column("rag_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("tool_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("model_config_id", sa.BigInteger(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("agent_config_id", sa.BigInteger(), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_config_id"], ["user_ai_model_configs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_conversations_user_deleted_last",
        "chat_conversations",
        ["user_id", "deleted_at", "last_message_at"],
    )
    op.create_index("ix_chat_conversations_capability", "chat_conversations", ["capability"])
    op.create_index("ix_chat_conversations_conversation_id", "chat_conversations", ["conversation_id"], unique=True)
    op.create_index("ix_chat_conversations_deleted_at", "chat_conversations", ["deleted_at"])
    op.create_index("ix_chat_conversations_last_message_at", "chat_conversations", ["last_message_at"])
    op.create_index("ix_chat_conversations_model_config_id", "chat_conversations", ["model_config_id"])
    op.create_index("ix_chat_conversations_user_id", "chat_conversations", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("conversation_db_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("capability", sa.String(length=50), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=True),
        sa.Column("execution_engine", sa.String(length=30), nullable=True),
        sa.Column("rag_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("tool_enabled", sa.Boolean(), server_default="false", nullable=False),
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
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_db_id"], ["chat_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_config_id"], ["user_ai_model_configs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_messages_conversation_index",
        "chat_messages",
        ["conversation_db_id", "message_index"],
        unique=True,
    )
    op.create_index("ix_chat_messages_capability", "chat_messages", ["capability"])
    op.create_index("ix_chat_messages_conversation_db_id", "chat_messages", ["conversation_db_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_chat_messages_message_id", "chat_messages", ["message_id"], unique=True)
    op.create_index("ix_chat_messages_model_config_id", "chat_messages", ["model_config_id"])
