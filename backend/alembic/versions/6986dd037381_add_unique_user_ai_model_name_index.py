"""add unique user ai model name index

Revision ID: 6986dd037381
Revises: 2d2814d023b5
Create Date: 2026-07-24 22:53:05.247753

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6986dd037381"
down_revision: Union[str, None] = "2d2814d023b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_user_ai_model_configs_user_model_active",
        "user_ai_model_configs",
        ["user_id", "model"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_ai_model_configs_user_model_active", table_name="user_ai_model_configs")
