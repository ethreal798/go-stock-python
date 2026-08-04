"""remove unused news entity details

Revision ID: 05b8cad2e567
Revises: f4a7b9c1d456
Create Date: 2026-08-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "05b8cad2e567"
down_revision: Union[str, None] = "f4a7b9c1d456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("news_item_entities", "metadata")
    op.drop_column("news_item_entities", "price_at_publish")
    op.drop_column("news_item_entities", "change_pct_at_publish")


def downgrade() -> None:
    op.add_column(
        "news_item_entities",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "news_item_entities",
        sa.Column("price_at_publish", sa.Numeric(20, 6), nullable=True),
    )
    op.add_column(
        "news_item_entities",
        sa.Column("change_pct_at_publish", sa.Numeric(12, 6), nullable=True),
    )
