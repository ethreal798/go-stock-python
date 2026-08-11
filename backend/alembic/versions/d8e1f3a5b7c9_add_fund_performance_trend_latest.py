"""add fund performance trend latest snapshots

Revision ID: d8e1f3a5b7c9
Revises: c5f7a9b3d421
Create Date: 2026-08-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d8e1f3a5b7c9"
down_revision: Union[str, None] = "c5f7a9b3d421"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fund_performance_trend_latest",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False, comment="系统标准周期编码"),
        sa.Column("start_date", sa.Date(), nullable=False, comment="曲线实际开始日期"),
        sa.Column("end_date", sa.Date(), nullable=False, comment="曲线实际结束日期"),
        sa.Column("series_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="完整曲线数组"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="eastmoney", comment="数据来源"),
        sa.Column("schema_version", sa.SmallInteger(), nullable=False, server_default="1", comment="JSON结构版本"),
        sa.Column("content_hash", sa.String(length=64), nullable=False, comment="规范化曲线内容 SHA-256"),
        sa.Column("point_count", sa.Integer(), nullable=False, comment="全部曲线点数合计"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="成功抓取时间"),
        sa.Column("expires_at", sa.DateTime(), nullable=False, comment="建议刷新时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "period IN ('1m', '3m', '6m', '1y', '3y', '5y', 'ytd', 'since_inception')",
            name="ck_fund_performance_trend_latest_period",
        ),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "period", name="uq_fund_performance_trend_latest_fund_period"),
    )
    op.create_index(
        "ix_fund_performance_trend_latest_expires_at",
        "fund_performance_trend_latest",
        ["expires_at"],
    )
    op.create_index(
        "ix_fund_performance_trend_latest_deleted_at",
        "fund_performance_trend_latest",
        ["deleted_at"],
    )


def downgrade() -> None:
    op.drop_table("fund_performance_trend_latest")
