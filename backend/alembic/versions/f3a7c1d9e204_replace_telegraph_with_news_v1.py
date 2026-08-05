"""replace telegraph storage with normalized news v1

Revision ID: f3a7c1d9e204
Revises: e1f7c9a4b203
Create Date: 2026-08-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f3a7c1d9e204"
down_revision: Union[str, None] = "e1f7c9a4b203"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 旧表没有来源记录 ID，无法可靠迁移到新唯一约束；按产品决定直接清理。
    op.execute("DELETE FROM rag_query_logs WHERE query_intent = 'news_qa'")
    op.execute("DELETE FROM rag_documents WHERE source_type IN ('telegraph', 'news', 'fast')")

    op.drop_table("telegraph_tags")
    op.drop_table("tags")
    op.drop_table("telegraph_list")

    news_sources = op.create_table(
        "news_sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False, comment="cls/wscn/sina"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="来源展示名称"),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_news_sources_code"),
    )
    op.bulk_insert(
        news_sources,
        [
            {"code": "cls", "name": "财联社", "enabled": True, "sort_order": 10},
            {"code": "wscn", "name": "华尔街见闻", "enabled": True, "sort_order": 20},
            {"code": "sina", "name": "新浪财经", "enabled": True, "sort_order": 30},
        ],
    )

    op.create_table(
        "news_raw_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("source_item_id", sa.String(length=128), nullable=False, comment="来源响应中的快讯 ID"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="单条快讯完整原始 JSON"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "source_item_id", name="uq_news_raw_source_item"),
    )
    op.create_index("ix_news_raw_items_source_id", "news_raw_items", ["source_id"], unique=False)
    op.create_index("ix_news_raw_items_published_at", "news_raw_items", ["published_at"], unique=False)
    op.create_index("ix_news_raw_source_published", "news_raw_items", ["source_id", "published_at"], unique=False)

    op.create_table(
        "news_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_item_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(length=32), server_default="flash", nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("content_more_text", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.String(length=1000), nullable=True),
        sa.Column("original_url", sa.String(length=1000), nullable=True),
        sa.Column("author_name", sa.String(length=200), nullable=True),
        sa.Column("source_importance_code", sa.String(length=32), nullable=True),
        sa.Column("is_source_important", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_focus", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_calendar", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["raw_item_id"], ["news_raw_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_item_id", name="uq_news_items_raw_item_id"),
    )
    op.create_index("ix_news_items_source_id", "news_items", ["source_id"], unique=False)
    op.create_index("ix_news_items_content_type", "news_items", ["content_type"], unique=False)
    op.create_index("ix_news_items_published_at", "news_items", ["published_at"], unique=False)
    op.create_index("ix_news_items_is_source_important", "news_items", ["is_source_important"], unique=False)
    op.create_index("ix_news_items_type_published", "news_items", ["content_type", "published_at", "id"])
    op.create_index("ix_news_items_source_published", "news_items", ["source_id", "published_at", "id"])
    op.create_index("ix_news_items_important_published", "news_items", ["is_source_important", "published_at"])

    op.create_table(
        "news_item_topics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("news_item_id", sa.BigInteger(), nullable=False),
        sa.Column("topic_type", sa.String(length=32), nullable=False, comment="channel/subject/theme/tag"),
        sa.Column("source_topic_id", sa.String(length=128), nullable=True),
        sa.Column("code", sa.String(length=128), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["news_item_id"], ["news_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("news_item_id", "topic_type", "name", name="uq_news_item_topic"),
    )
    op.create_index("ix_news_item_topics_news_item_id", "news_item_topics", ["news_item_id"])
    op.create_index("ix_news_item_topics_topic_type", "news_item_topics", ["topic_type"])
    op.create_index("ix_news_item_topics_name", "news_item_topics", ["name"])
    op.create_index("ix_news_topics_type_name", "news_item_topics", ["topic_type", "name"])

    op.create_table(
        "news_item_entities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("news_item_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=True),
        sa.Column("source_symbol", sa.String(length=100), nullable=True),
        sa.Column("normalized_symbol", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("price_at_publish", sa.Numeric(20, 6), nullable=True),
        sa.Column("change_pct_at_publish", sa.Numeric(12, 6), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["news_item_id"], ["news_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("news_item_id", "entity_type", "source_symbol", name="uq_news_item_entity"),
    )
    op.create_index("ix_news_item_entities_news_item_id", "news_item_entities", ["news_item_id"])
    op.create_index("ix_news_item_entities_entity_type", "news_item_entities", ["entity_type"])
    op.create_index("ix_news_item_entities_market", "news_item_entities", ["market"])
    op.create_index("ix_news_item_entities_normalized_symbol", "news_item_entities", ["normalized_symbol"])
    op.create_index("ix_news_item_entities_name", "news_item_entities", ["name"])
    op.create_index("ix_news_entities_normalized_type", "news_item_entities", ["normalized_symbol", "entity_type"])

    op.create_table(
        "news_item_relations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("news_item_id", sa.BigInteger(), nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("source_related_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("url", sa.String(length=1500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["news_item_id"], ["news_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("news_item_id", "relation_type", "source_related_id", "url", name="uq_news_item_relation"),
    )
    op.create_index("ix_news_item_relations_news_item_id", "news_item_relations", ["news_item_id"])
    op.create_index("ix_news_item_relations_relation_type", "news_item_relations", ["relation_type"])


def downgrade() -> None:
    op.drop_table("news_item_relations")
    op.drop_table("news_item_entities")
    op.drop_table("news_item_topics")
    op.drop_table("news_items")
    op.drop_table("news_raw_items")
    op.drop_table("news_sources")

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
        sa.Column("type", sa.String(length=20), nullable=True),
        sa.Column("is_relevant", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("relevance_score", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
    )
    op.create_table(
        "telegraph_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("tag_id", sa.BigInteger(), sa.ForeignKey("tags.id"), nullable=True),
        sa.Column("telegraph_id", sa.BigInteger(), sa.ForeignKey("telegraph_list.id"), nullable=True),
    )
