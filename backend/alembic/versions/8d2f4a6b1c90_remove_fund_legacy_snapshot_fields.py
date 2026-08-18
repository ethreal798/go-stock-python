"""remove legacy snapshot fields from funds

Revision ID: 8d2f4a6b1c90
Revises: 7c1e9a4b2d60
Create Date: 2026-08-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8d2f4a6b1c90"
down_revision: Union[str, None] = "7c1e9a4b2d60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_COLUMNS = (
    ("nav", sa.Float(), "单位净值"),
    ("acc_nav", sa.Float(), "累计净值"),
    ("day_growth", sa.Float(), "日增长率(%)"),
    ("week_growth", sa.Float(), "近一周增长率(%)"),
    ("month_growth", sa.Float(), "近一月增长率(%)"),
    ("three_month_growth", sa.Float(), "近三月增长率(%)"),
    ("six_month_growth", sa.Float(), "近六月增长率(%)"),
    ("year_growth", sa.Float(), "近一年增长率(%)"),
    ("current_year_growth", sa.Float(), "今年以来增长率(%)"),
    ("manager", sa.String(length=100), "基金经理"),
    ("last_update", sa.DateTime(), "最后更新时间"),
)


def upgrade() -> None:
    for column_name, _, _ in LEGACY_COLUMNS:
        op.drop_column("funds", column_name)


def downgrade() -> None:
    for column_name, column_type, comment in LEGACY_COLUMNS:
        op.add_column("funds", sa.Column(column_name, column_type, nullable=True, comment=comment))
