"""add is_exchange column to funds

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-17 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("funds", sa.Column("is_exchange", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否场内基金"))
    op.create_index("ix_funds_is_exchange", "funds", ["is_exchange"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_funds_is_exchange", table_name="funds")
    op.drop_column("funds", "is_exchange")
