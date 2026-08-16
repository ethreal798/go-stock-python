"""remove fund category status last_seen columns

Revision ID: a1b2c3d4e5f6
Revises: d5be034c0849
Create Date: 2026-08-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d5be034c0849"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("funds", "category")
    op.drop_column("funds", "status")
    op.drop_column("funds", "last_seen_data_date")
    op.drop_column("funds", "last_seen_at")


def downgrade() -> None:
    op.add_column("funds", sa.Column("last_seen_at", sa.DateTime(), nullable=True, comment="最近一次在排行中出现的抓取时间"))
    op.add_column("funds", sa.Column("last_seen_data_date", sa.Date(), nullable=True, comment="最近一次在排行中出现的数据日期"))
    op.add_column("funds", sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown", comment="排行可观测状态"))
    op.add_column("funds", sa.Column("category", sa.String(length=20), nullable=False, server_default="unknown", comment="数据路由分类"))
    op.create_index(op.f("ix_funds_last_seen_data_date"), "funds", ["last_seen_data_date"], unique=False)
    op.create_index(op.f("ix_funds_status"), "funds", ["status"], unique=False)
    op.create_index(op.f("ix_funds_category"), "funds", ["category"], unique=False)
