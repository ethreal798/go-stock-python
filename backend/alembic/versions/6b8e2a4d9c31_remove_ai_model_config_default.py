"""remove_ai_model_config_default

Revision ID: 6b8e2a4d9c31
Revises: 2d7f5c9e0a13
Create Date: 2026-07-24 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6b8e2a4d9c31"
down_revision: Union[str, None] = "2d7f5c9e0a13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("uq_user_ai_model_configs_user_default_active", table_name="user_ai_model_configs")
    op.drop_column("user_ai_model_configs", "is_default")


def downgrade() -> None:
    op.add_column(
        "user_ai_model_configs",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否默认配置",
        ),
    )
    op.create_index(
        "uq_user_ai_model_configs_user_default_active",
        "user_ai_model_configs",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true AND deleted_at IS NULL"),
    )
