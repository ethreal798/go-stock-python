"""add_user_ai_model_configs

Revision ID: 2d7f5c9e0a13
Revises: 9f2b7d1c4a6e
Create Date: 2026-07-19 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2d7f5c9e0a13"
down_revision: Union[str, None] = "9f2b7d1c4a6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_ai_model_configs",
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="配置名称"),
        sa.Column("provider", sa.String(length=50), nullable=False, comment="供应商标识"),
        sa.Column("base_url", sa.String(length=500), nullable=False, comment="OpenAI兼容接口Base URL"),
        sa.Column("model", sa.String(length=100), nullable=False, comment="模型名称"),
        sa.Column("api_key_ciphertext", sa.Text(), nullable=True, comment="加密后的API Key"),
        sa.Column("api_key_hint", sa.String(length=32), nullable=True, comment="API Key脱敏提示"),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False, comment="最大输出Token数"),
        sa.Column("temperature", sa.Float(), nullable=False, comment="温度参数"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, comment="请求超时时间"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="是否启用"),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否默认配置",
        ),
        sa.Column("extra_config", sa.JSON(), nullable=True, comment="扩展配置"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("max_output_tokens >= 1 AND max_output_tokens <= 128000", name="ck_ai_cfg_tokens_range"),
        sa.CheckConstraint("temperature >= 0 AND temperature <= 2", name="ck_ai_cfg_temperature_range"),
        sa.CheckConstraint("timeout_seconds >= 1 AND timeout_seconds <= 300", name="ck_ai_cfg_timeout_range"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_ai_model_configs_deleted_at"), "user_ai_model_configs", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_user_ai_model_configs_user_id"), "user_ai_model_configs", ["user_id"], unique=False)
    op.create_index(
        "uq_user_ai_model_configs_user_name_active",
        "user_ai_model_configs",
        ["user_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_user_ai_model_configs_user_default_active",
        "user_ai_model_configs",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_ai_model_configs_user_default_active", table_name="user_ai_model_configs")
    op.drop_index("uq_user_ai_model_configs_user_name_active", table_name="user_ai_model_configs")
    op.drop_index(op.f("ix_user_ai_model_configs_user_id"), table_name="user_ai_model_configs")
    op.drop_index(op.f("ix_user_ai_model_configs_deleted_at"), table_name="user_ai_model_configs")
    op.drop_table("user_ai_model_configs")
