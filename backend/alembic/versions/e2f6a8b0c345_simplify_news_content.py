"""simplify news content storage

Revision ID: e2f6a8b0c345
Revises: d1e5f7a9b234
Create Date: 2026-08-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e2f6a8b0c345"
down_revision: Union[str, None] = "d1e5f7a9b234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "news_items",
        "content_text",
        existing_type=sa.Text(),
        existing_nullable=False,
        new_column_name="content",
    )
    op.execute("""
        UPDATE news_items
        SET content = content || CASE
            WHEN nullif(btrim(content_more_text), '') IS NOT NULL
                THEN E'\n\n' || btrim(content_more_text)
            ELSE ''
        END
        """)

    op.drop_column("news_items", "summary")
    op.drop_column("news_items", "content_html")
    op.drop_column("news_items", "content_more_text")
    op.drop_column("news_items", "author_name")


def downgrade() -> None:
    op.add_column("news_items", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("news_items", sa.Column("content_html", sa.Text(), nullable=True))
    op.add_column("news_items", sa.Column("content_more_text", sa.Text(), nullable=True))
    op.add_column("news_items", sa.Column("author_name", sa.String(length=200), nullable=True))
    op.alter_column(
        "news_items",
        "content",
        existing_type=sa.Text(),
        existing_nullable=False,
        new_column_name="content_text",
    )
