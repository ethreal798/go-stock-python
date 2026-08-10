"""add fund exchange nav history table

Revision ID: b4e6f8a2c310
Revises: 9a3b5c7d1e20
Create Date: 2026-08-08 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b4e6f8a2c310"
down_revision: Union[str, None] = "9a3b5c7d1e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fund_exchange_nav_history",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("data_date", sa.Date(), nullable=False, comment="净值日期"),
        sa.Column("unit_nav", sa.Numeric(18, 8), nullable=True, comment="单位净值"),
        sa.Column("accumulated_nav", sa.Numeric(18, 8), nullable=True, comment="累计净值"),
        sa.Column("daily_growth_pct", sa.Numeric(12, 6), nullable=True, comment="日增长率(%)"),
        sa.Column("purchase_status", sa.String(length=50), nullable=True, comment="申购状态"),
        sa.Column("redemption_status", sa.String(length=50), nullable=True, comment="赎回状态"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "data_date", name="uq_fund_exchange_nav_history_fund_date"),
    )
    op.create_index("ix_fund_exchange_nav_history_data_date", "fund_exchange_nav_history", ["data_date"])
    op.create_index("ix_fund_exchange_nav_history_deleted_at", "fund_exchange_nav_history", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("fund_exchange_nav_history")
