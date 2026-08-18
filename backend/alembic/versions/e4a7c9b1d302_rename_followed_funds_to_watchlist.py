"""rename followed funds to fund watchlist items

Revision ID: e4a7c9b1d302
Revises: d8e1f3a5b7c9
Create Date: 2026-08-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e4a7c9b1d302"
down_revision: Union[str, None] = "d8e1f3a5b7c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """保留现有自选数据，仅重命名表和索引。"""
    op.rename_table("followed_funds", "fund_watchlist_items")
    op.execute("ALTER TABLE fund_watchlist_items " "RENAME CONSTRAINT followed_funds_pkey TO fund_watchlist_items_pkey")
    op.execute("ALTER SEQUENCE IF EXISTS followed_funds_id_seq RENAME TO fund_watchlist_items_id_seq")
    op.execute("ALTER INDEX ix_followed_funds_deleted_at RENAME TO ix_fund_watchlist_items_deleted_at")
    op.execute("ALTER INDEX ix_followed_funds_fund_code RENAME TO ix_fund_watchlist_items_fund_code")
    op.execute("ALTER INDEX ix_followed_funds_user_id RENAME TO ix_fund_watchlist_items_user_id")


def downgrade() -> None:
    op.execute("ALTER INDEX ix_fund_watchlist_items_user_id RENAME TO ix_followed_funds_user_id")
    op.execute("ALTER INDEX ix_fund_watchlist_items_fund_code RENAME TO ix_followed_funds_fund_code")
    op.execute("ALTER INDEX ix_fund_watchlist_items_deleted_at RENAME TO ix_followed_funds_deleted_at")
    op.execute("ALTER SEQUENCE IF EXISTS fund_watchlist_items_id_seq RENAME TO followed_funds_id_seq")
    op.execute("ALTER TABLE fund_watchlist_items " "RENAME CONSTRAINT fund_watchlist_items_pkey TO followed_funds_pkey")
    op.rename_table("fund_watchlist_items", "followed_funds")
