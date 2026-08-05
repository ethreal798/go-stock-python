"""simplify news item topics to names only

Revision ID: a8b2c4d6e901
Revises: f3a7c1d9e204
Create Date: 2026-08-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a8b2c4d6e901"
down_revision: Union[str, None] = "f3a7c1d9e204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_news_topics_type_name", table_name="news_item_topics")
    op.drop_index("ix_news_item_topics_topic_type", table_name="news_item_topics")
    op.drop_constraint("uq_news_item_topic", "news_item_topics", type_="unique")
    op.create_unique_constraint("uq_news_item_topic", "news_item_topics", ["news_item_id", "name"])

    op.drop_column("news_item_topics", "topic_type")
    op.drop_column("news_item_topics", "source_topic_id")
    op.drop_column("news_item_topics", "code")
    op.drop_column("news_item_topics", "metadata")


def downgrade() -> None:
    op.add_column(
        "news_item_topics",
        sa.Column("topic_type", sa.String(length=32), server_default="topic", nullable=False),
    )
    op.add_column("news_item_topics", sa.Column("source_topic_id", sa.String(length=128), nullable=True))
    op.add_column("news_item_topics", sa.Column("code", sa.String(length=128), nullable=True))
    op.add_column(
        "news_item_topics",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.drop_constraint("uq_news_item_topic", "news_item_topics", type_="unique")
    op.create_unique_constraint(
        "uq_news_item_topic",
        "news_item_topics",
        ["news_item_id", "topic_type", "name"],
    )
    op.create_index("ix_news_item_topics_topic_type", "news_item_topics", ["topic_type"])
    op.create_index("ix_news_topics_type_name", "news_item_topics", ["topic_type", "name"])
    op.alter_column("news_item_topics", "topic_type", server_default=None)
