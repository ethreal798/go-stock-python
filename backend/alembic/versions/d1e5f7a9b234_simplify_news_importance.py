"""simplify news importance fields and rules

Revision ID: d1e5f7a9b234
Revises: c0d4e6f8a123
Create Date: 2026-08-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d1e5f7a9b234"
down_revision: Union[str, None] = "c0d4e6f8a123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Recalculate historical records from raw payloads using the finalized source rules.
    op.execute("""
        UPDATE news_items AS item
        SET is_source_important = CASE source.code
            WHEN 'cls' THEN upper(coalesce(raw.payload ->> 'level', '')) IN ('A', 'B')
            WHEN 'wscn' THEN CASE
                WHEN coalesce(raw.payload ->> 'score', '') ~ '^-?[0-9]+([.][0-9]+)?$'
                    THEN (raw.payload ->> 'score')::numeric >= 2
                ELSE false
            END
            WHEN 'sina' THEN EXISTS (
                SELECT 1
                FROM jsonb_array_elements(
                    CASE
                        WHEN jsonb_typeof(raw.payload -> 'tag') = 'array' THEN raw.payload -> 'tag'
                        ELSE '[]'::jsonb
                    END
                ) AS tag
                WHERE tag ->> 'name' = '焦点'
            )
            ELSE false
        END
        FROM news_raw_items AS raw, news_sources AS source
        WHERE item.raw_item_id = raw.id
          AND item.source_id = source.id
        """)

    op.drop_column("news_items", "source_importance_code")
    op.drop_column("news_items", "is_pinned")
    op.drop_column("news_items", "is_focus")
    op.drop_column("news_items", "is_calendar")


def downgrade() -> None:
    op.add_column("news_items", sa.Column("source_importance_code", sa.String(length=32), nullable=True))
    op.add_column(
        "news_items",
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "news_items",
        sa.Column("is_focus", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "news_items",
        sa.Column("is_calendar", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
