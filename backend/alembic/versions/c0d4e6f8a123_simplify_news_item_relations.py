"""simplify news item relations to original urls

Revision ID: c0d4e6f8a123
Revises: b9c3d5e7f012
Create Date: 2026-08-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c0d4e6f8a123"
down_revision: Union[str, None] = "b9c3d5e7f012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This table now represents original documents only.
    op.execute("""
        DELETE FROM news_item_relations
        WHERE relation_type <> 'original_document'
           OR url IS NULL
           OR btrim(url) = ''
        """)
    op.execute("""
        DELETE FROM news_item_relations AS relation
        USING news_item_relations AS duplicate
        WHERE relation.news_item_id = duplicate.news_item_id
          AND relation.url = duplicate.url
          AND relation.id > duplicate.id
        """)

    op.drop_index("ix_news_item_relations_relation_type", table_name="news_item_relations")
    op.drop_constraint("uq_news_item_relation", "news_item_relations", type_="unique")
    op.create_unique_constraint("uq_news_item_relation", "news_item_relations", ["news_item_id", "url"])
    op.alter_column("news_item_relations", "url", existing_type=sa.String(length=1500), nullable=False)

    op.drop_column("news_item_relations", "content")
    op.drop_column("news_item_relations", "source_related_id")
    op.drop_column("news_item_relations", "title")
    op.drop_column("news_item_relations", "relation_type")
    op.drop_column("news_item_relations", "metadata")


def downgrade() -> None:
    op.add_column(
        "news_item_relations",
        sa.Column(
            "relation_type",
            sa.String(length=32),
            server_default="original_document",
            nullable=False,
        ),
    )
    op.add_column("news_item_relations", sa.Column("source_related_id", sa.String(length=128), nullable=True))
    op.add_column("news_item_relations", sa.Column("title", sa.String(length=500), nullable=True))
    op.add_column("news_item_relations", sa.Column("content", sa.Text(), nullable=True))
    op.add_column(
        "news_item_relations",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.drop_constraint("uq_news_item_relation", "news_item_relations", type_="unique")
    op.create_unique_constraint(
        "uq_news_item_relation",
        "news_item_relations",
        ["news_item_id", "relation_type", "source_related_id", "url"],
    )
    op.create_index("ix_news_item_relations_relation_type", "news_item_relations", ["relation_type"])
    op.alter_column("news_item_relations", "url", existing_type=sa.String(length=1500), nullable=True)
    op.alter_column("news_item_relations", "relation_type", server_default=None)
