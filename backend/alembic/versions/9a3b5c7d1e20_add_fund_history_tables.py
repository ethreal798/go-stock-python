"""add fund open nav and money yield history tables

Revision ID: 9a3b5c7d1e20
Revises: 8d2f4a6b1c90
Create Date: 2026-08-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a3b5c7d1e20"
down_revision: Union[str, None] = "8d2f4a6b1c90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    ]


def _create_history_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_data_date", table_name, ["data_date"])
    op.create_index(f"ix_{table_name}_deleted_at", table_name, ["deleted_at"])


def upgrade() -> None:
    op.create_table(
        "fund_open_nav_history",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("data_date", sa.Date(), nullable=False, comment="净值日期"),
        sa.Column("unit_nav", sa.Numeric(18, 8), nullable=True, comment="单位净值"),
        sa.Column("accumulated_nav", sa.Numeric(18, 8), nullable=True, comment="累计净值"),
        sa.Column("daily_growth_pct", sa.Numeric(12, 6), nullable=True, comment="日增长率(%)"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "data_date", name="uq_fund_open_nav_history_fund_date"),
    )
    _create_history_indexes("fund_open_nav_history")

    op.create_table(
        "fund_money_yield_history",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("data_date", sa.Date(), nullable=False, comment="收益日期"),
        sa.Column("income_per_10k", sa.Numeric(18, 8), nullable=True, comment="每万份收益（元）"),
        sa.Column("annualized_7d_pct", sa.Numeric(12, 6), nullable=True, comment="七日年化收益率(%)"),
        sa.Column("purchase_status", sa.String(length=50), nullable=True, comment="申购状态"),
        sa.Column("redemption_status", sa.String(length=50), nullable=True, comment="赎回状态"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "data_date", name="uq_fund_money_yield_history_fund_date"),
    )
    _create_history_indexes("fund_money_yield_history")


def downgrade() -> None:
    op.drop_table("fund_money_yield_history")
    op.drop_table("fund_open_nav_history")
