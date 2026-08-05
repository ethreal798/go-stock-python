"""move news original urls to relations

Revision ID: b9c3d5e7f012
Revises: a8b2c4d6e901
Create Date: 2026-08-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b9c3d5e7f012"
down_revision: Union[str, None] = "a8b2c4d6e901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Preserve external documents in the relation table before dropping main-table URLs.
    op.execute("""
        INSERT INTO news_item_relations (
            news_item_id,
            relation_type,
            url,
            created_at
        )
        SELECT
            item.id,
            'original_document',
            item.original_url,
            now()
        FROM news_items AS item
        WHERE item.original_url IS NOT NULL
          AND btrim(item.original_url) <> ''
          AND NOT EXISTS (
              SELECT 1
              FROM news_item_relations AS relation
              WHERE relation.news_item_id = item.id
                AND relation.relation_type = 'original_document'
                AND relation.url = item.original_url
          )
        """)

    op.drop_column("news_items", "canonical_url")
    op.drop_column("news_items", "original_url")


def downgrade() -> None:
    op.add_column("news_items", sa.Column("canonical_url", sa.String(length=1000), nullable=True))
    op.add_column("news_items", sa.Column("original_url", sa.String(length=1000), nullable=True))
    op.execute("""
        UPDATE news_items AS item
        SET original_url = (
            SELECT relation.url
            FROM news_item_relations AS relation
            WHERE relation.news_item_id = item.id
              AND relation.relation_type = 'original_document'
              AND relation.url IS NOT NULL
            ORDER BY relation.id
            LIMIT 1
        )
        """)
