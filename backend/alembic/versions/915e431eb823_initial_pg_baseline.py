"""initial_pg_baseline

Revision ID: 915e431eb823
Revises:
Create Date: 2026-05-29 23:49:12.951612

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "915e431eb823"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegraph_list",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("time", sa.String(length=50), nullable=True),
        sa.Column("data_time", sa.DateTime(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("is_red", sa.Boolean(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("sentiment_result", sa.String(length=50), nullable=True),
    )
    op.create_index(op.f("ix_telegraph_list_data_time"), "telegraph_list", ["data_time"], unique=False)
    op.create_index(op.f("ix_telegraph_list_title"), "telegraph_list", ["title"], unique=False)
    op.create_index(op.f("ix_telegraph_list_content"), "telegraph_list", ["content"], unique=False)
    op.create_index(op.f("ix_telegraph_list_is_red"), "telegraph_list", ["is_red"], unique=False)
    op.create_index(op.f("ix_telegraph_list_source"), "telegraph_list", ["source"], unique=False)
    op.create_index(op.f("ix_telegraph_list_sentiment_result"), "telegraph_list", ["sentiment_result"], unique=False)
    op.create_index(op.f("ix_telegraph_list_deleted_at"), "telegraph_list", ["deleted_at"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
    )
    op.create_index(op.f("ix_tags_deleted_at"), "tags", ["deleted_at"], unique=False)

    op.create_table(
        "telegraph_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("tag_id", sa.BigInteger(), sa.ForeignKey("tags.id"), nullable=True),
        sa.Column("telegraph_id", sa.BigInteger(), sa.ForeignKey("telegraph_list.id"), nullable=True),
    )
    op.create_index(op.f("ix_telegraph_tags_deleted_at"), "telegraph_tags", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_telegraph_tags_deleted_at"), table_name="telegraph_tags")
    op.drop_table("telegraph_tags")
    op.drop_index(op.f("ix_tags_deleted_at"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_telegraph_list_deleted_at"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_sentiment_result"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_source"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_is_red"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_content"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_title"), table_name="telegraph_list")
    op.drop_index(op.f("ix_telegraph_list_data_time"), table_name="telegraph_list")
    op.drop_table("telegraph_list")
