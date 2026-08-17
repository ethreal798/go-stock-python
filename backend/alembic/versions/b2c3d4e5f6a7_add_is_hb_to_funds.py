"""add is_hb column to funds

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("funds", sa.Column("is_hb", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否货币基金"))
    op.create_index("ix_funds_is_hb", "funds", ["is_hb"], unique=False)
    # 回填数据：名称包含"货币"且类型包含"货币型"
    op.execute("""
        UPDATE funds
        SET is_hb = true
        WHERE name LIKE '%货币%' AND type LIKE '%货币型%'
    """)


def downgrade() -> None:
    op.drop_index("ix_funds_is_hb", table_name="funds")
    op.drop_column("funds", "is_hb")
