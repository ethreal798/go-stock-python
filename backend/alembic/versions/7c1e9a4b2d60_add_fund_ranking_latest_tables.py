"""add fund ranking latest tables

Revision ID: 7c1e9a4b2d60
Revises: 05b8cad2e567
Create Date: 2026-08-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7c1e9a4b2d60"
down_revision: Union[str, None] = "05b8cad2e567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    ]


def _common_rank_columns(data_date_comment: str) -> list[sa.Column]:
    return [
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("fund_name", sa.String(length=200), nullable=False, comment="来源基金简称"),
        sa.Column("data_date", sa.Date(), nullable=True, comment=data_date_comment),
    ]


def _return_columns(*periods: str) -> list[sa.Column]:
    labels = {
        "1w": "近1周",
        "1m": "近1月",
        "3m": "近3月",
        "6m": "近6月",
        "1y": "近1年",
        "2y": "近2年",
        "3y": "近3年",
        "5y": "近5年",
        "ytd": "今年以来",
        "since_inception": "成立以来",
    }
    return [
        sa.Column(
            f"return_{period}_pct",
            sa.Numeric(12, 6),
            nullable=True,
            comment=f"{labels[period]}收益率(%)",
        )
        for period in periods
    ]


def _create_common_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_deleted_at", table_name, ["deleted_at"])
    op.create_index(f"ix_{table_name}_fund_id", table_name, ["fund_id"], unique=True)
    op.create_index(f"ix_{table_name}_fund_code", table_name, ["fund_code"], unique=True)
    op.create_index(f"ix_{table_name}_data_date", table_name, ["data_date"])


def upgrade() -> None:
    op.alter_column("funds", "name", existing_type=sa.String(length=100), type_=sa.String(length=200))
    op.add_column(
        "funds",
        sa.Column("category", sa.String(length=20), server_default="unknown", nullable=False, comment="数据路由分类"),
    )
    op.add_column(
        "funds",
        sa.Column("status", sa.String(length=20), server_default="unknown", nullable=False, comment="排行可观测状态"),
    )
    op.add_column(
        "funds",
        sa.Column("last_seen_data_date", sa.Date(), nullable=True, comment="最近一次在排行中出现的数据日期"),
    )
    op.add_column(
        "funds",
        sa.Column("last_seen_at", sa.DateTime(), nullable=True, comment="最近一次在排行中出现的抓取时间"),
    )
    op.create_index("ix_funds_category", "funds", ["category"])
    op.create_index("ix_funds_status", "funds", ["status"])
    op.create_index("ix_funds_last_seen_data_date", "funds", ["last_seen_data_date"])

    op.create_table(
        "fund_open_rank_latest",
        *_common_rank_columns("净值日期；尚未披露时为空"),
        sa.Column("unit_nav", sa.Numeric(18, 8), nullable=True, comment="单位净值"),
        sa.Column("accumulated_nav", sa.Numeric(18, 8), nullable=True, comment="累计净值"),
        sa.Column("daily_growth_pct", sa.Numeric(12, 6), nullable=True, comment="日增长率(%)"),
        *_return_columns("1w", "1m", "3m", "6m", "1y", "2y", "3y", "ytd", "since_inception"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("fund_open_rank_latest")

    op.create_table(
        "fund_exchange_rank_latest",
        *_common_rank_columns("净值日期；尚未披露时为空"),
        sa.Column("fund_type", sa.String(length=50), nullable=True, comment="东方财富场内基金类型"),
        sa.Column("unit_nav", sa.Numeric(18, 8), nullable=True, comment="单位净值"),
        sa.Column("accumulated_nav", sa.Numeric(18, 8), nullable=True, comment="累计净值"),
        *_return_columns("1w", "1m", "3m", "6m", "1y", "2y", "3y", "ytd", "since_inception"),
        sa.Column("inception_date", sa.Date(), nullable=True, comment="成立日期"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("fund_exchange_rank_latest")

    op.create_table(
        "fund_money_rank_latest",
        *_common_rank_columns("收益日期；尚未披露时为空"),
        sa.Column("income_per_10k", sa.Numeric(18, 8), nullable=True, comment="万份收益(元/万份，非百分比)"),
        sa.Column("annualized_7d_pct", sa.Numeric(12, 6), nullable=True, comment="7日年化收益率(%)"),
        sa.Column("annualized_14d_pct", sa.Numeric(12, 6), nullable=True, comment="14日年化收益率(%)"),
        sa.Column("annualized_28d_pct", sa.Numeric(12, 6), nullable=True, comment="28日年化收益率(%)"),
        *_return_columns("1m", "3m", "6m", "1y", "2y", "3y", "5y", "ytd", "since_inception"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_common_indexes("fund_money_rank_latest")


def downgrade() -> None:
    for table_name in (
        "fund_money_rank_latest",
        "fund_exchange_rank_latest",
        "fund_open_rank_latest",
    ):
        op.drop_table(table_name)

    op.drop_index("ix_funds_last_seen_data_date", table_name="funds")
    op.drop_index("ix_funds_status", table_name="funds")
    op.drop_index("ix_funds_category", table_name="funds")
    op.drop_column("funds", "last_seen_at")
    op.drop_column("funds", "last_seen_data_date")
    op.drop_column("funds", "status")
    op.drop_column("funds", "category")
    op.alter_column("funds", "name", existing_type=sa.String(length=200), type_=sa.String(length=100))
