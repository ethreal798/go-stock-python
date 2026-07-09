"""add_rag_tables

Revision ID: 9f2b7d1c4a6e
Revises: bcadacaba706
Create Date: 2026-07-08 11:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "9f2b7d1c4a6e"
down_revision: Union[str, None] = "bcadacaba706"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_documents",
        sa.Column("source_type", sa.String(length=50), nullable=False, comment="来源类型: telegraph/news/notice/report"),
        sa.Column("source_id", sa.BigInteger(), nullable=False, comment="来源记录ID"),
        sa.Column("title", sa.String(length=500), nullable=True, comment="文档标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="文档正文"),
        sa.Column("content_hash", sa.String(length=64), nullable=False, comment="正文哈希"),
        sa.Column("summary", sa.Text(), nullable=True, comment="预生成摘要"),
        sa.Column("published_at", sa.DateTime(), nullable=True, comment="发布时间"),
        sa.Column("source_name", sa.String(length=100), nullable=True, comment="来源名称"),
        sa.Column("url", sa.String(length=500), nullable=True, comment="原文链接"),
        sa.Column("category", sa.String(length=50), nullable=True, comment="新闻分类"),
        sa.Column("importance_score", sa.Integer(), nullable=True, server_default="0", comment="重要性评分"),
        sa.Column("sentiment", sa.String(length=50), nullable=True, comment="情绪标签"),
        sa.Column("language", sa.String(length=20), nullable=True, server_default="zh", comment="语言"),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="pending", comment="处理状态"),
        sa.Column("extra_metadata", sa.JSON(), nullable=True, comment="扩展元数据"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rag_documents_source", "rag_documents", ["source_type", "source_id"], unique=False)
    op.create_index(op.f("ix_rag_documents_category"), "rag_documents", ["category"], unique=False)
    op.create_index(op.f("ix_rag_documents_content_hash"), "rag_documents", ["content_hash"], unique=False)
    op.create_index(op.f("ix_rag_documents_deleted_at"), "rag_documents", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_rag_documents_published_at"), "rag_documents", ["published_at"], unique=False)
    op.create_index(op.f("ix_rag_documents_sentiment"), "rag_documents", ["sentiment"], unique=False)
    op.create_index(op.f("ix_rag_documents_source_id"), "rag_documents", ["source_id"], unique=False)
    op.create_index(op.f("ix_rag_documents_source_name"), "rag_documents", ["source_name"], unique=False)
    op.create_index(op.f("ix_rag_documents_source_type"), "rag_documents", ["source_type"], unique=False)
    op.create_index(op.f("ix_rag_documents_status"), "rag_documents", ["status"], unique=False)

    op.create_table(
        "rag_chunks",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, comment="文档内块序号"),
        sa.Column("chunk_text", sa.Text(), nullable=False, comment="分块内容"),
        sa.Column("chunk_hash", sa.String(length=64), nullable=False, comment="分块哈希"),
        sa.Column("token_count", sa.Integer(), nullable=True, server_default="0", comment="估算 token 数"),
        sa.Column("start_offset", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("end_offset", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("source_name", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("importance_score", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True, comment="块级元数据"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rag_chunks_doc_chunk", "rag_chunks", ["document_id", "chunk_index"], unique=True)
    op.create_index(op.f("ix_rag_chunks_category"), "rag_chunks", ["category"], unique=False)
    op.create_index(op.f("ix_rag_chunks_chunk_hash"), "rag_chunks", ["chunk_hash"], unique=False)
    op.create_index(op.f("ix_rag_chunks_deleted_at"), "rag_chunks", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_rag_chunks_document_id"), "rag_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_rag_chunks_published_at"), "rag_chunks", ["published_at"], unique=False)
    op.create_index(op.f("ix_rag_chunks_sentiment"), "rag_chunks", ["sentiment"], unique=False)
    op.create_index(op.f("ix_rag_chunks_source_name"), "rag_chunks", ["source_name"], unique=False)

    op.create_table(
        "rag_chunk_embeddings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("embedding_vector", Vector(dim=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["rag_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rag_chunk_embeddings_chunk_model",
        "rag_chunk_embeddings",
        ["chunk_id", "embedding_model"],
        unique=True,
    )
    op.create_index(op.f("ix_rag_chunk_embeddings_chunk_id"), "rag_chunk_embeddings", ["chunk_id"], unique=False)
    op.create_index(
        op.f("ix_rag_chunk_embeddings_embedding_model"),
        "rag_chunk_embeddings",
        ["embedding_model"],
        unique=False,
    )

    op.create_table(
        "rag_entities",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_id", sa.BigInteger(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False, comment="stock/industry/concept/macro/person/org"),
        sa.Column("entity_name", sa.String(length=200), nullable=False),
        sa.Column("entity_code", sa.String(length=50), nullable=True),
        sa.Column("alias", sa.String(length=200), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True, server_default="0", comment="实体权重"),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chunk_id"], ["rag_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rag_entities_type_name", "rag_entities", ["entity_type", "entity_name"], unique=False)
    op.create_index(op.f("ix_rag_entities_chunk_id"), "rag_entities", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_rag_entities_deleted_at"), "rag_entities", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_rag_entities_document_id"), "rag_entities", ["document_id"], unique=False)
    op.create_index(op.f("ix_rag_entities_entity_code"), "rag_entities", ["entity_code"], unique=False)
    op.create_index(op.f("ix_rag_entities_entity_name"), "rag_entities", ["entity_name"], unique=False)
    op.create_index(op.f("ix_rag_entities_entity_type"), "rag_entities", ["entity_type"], unique=False)

    op.create_table(
        "rag_query_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("query_intent", sa.String(length=50), nullable=True),
        sa.Column("query_filters", sa.JSON(), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rag_query_logs_conversation_id"), "rag_query_logs", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_rag_query_logs_created_at"), "rag_query_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_rag_query_logs_model_name"), "rag_query_logs", ["model_name"], unique=False)
    op.create_index(op.f("ix_rag_query_logs_query_intent"), "rag_query_logs", ["query_intent"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rag_query_logs_query_intent"), table_name="rag_query_logs")
    op.drop_index(op.f("ix_rag_query_logs_model_name"), table_name="rag_query_logs")
    op.drop_index(op.f("ix_rag_query_logs_created_at"), table_name="rag_query_logs")
    op.drop_index(op.f("ix_rag_query_logs_conversation_id"), table_name="rag_query_logs")
    op.drop_table("rag_query_logs")

    op.drop_index(op.f("ix_rag_entities_entity_type"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_entity_name"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_entity_code"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_document_id"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_deleted_at"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_chunk_id"), table_name="rag_entities")
    op.drop_index("idx_rag_entities_type_name", table_name="rag_entities")
    op.drop_table("rag_entities")

    op.drop_index(op.f("ix_rag_chunk_embeddings_embedding_model"), table_name="rag_chunk_embeddings")
    op.drop_index(op.f("ix_rag_chunk_embeddings_chunk_id"), table_name="rag_chunk_embeddings")
    op.drop_index("idx_rag_chunk_embeddings_chunk_model", table_name="rag_chunk_embeddings")
    op.drop_table("rag_chunk_embeddings")

    op.drop_index(op.f("ix_rag_chunks_source_name"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_sentiment"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_published_at"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_document_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_deleted_at"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_chunk_hash"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_category"), table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_doc_chunk", table_name="rag_chunks")
    op.drop_table("rag_chunks")

    op.drop_index(op.f("ix_rag_documents_status"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_source_type"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_source_name"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_source_id"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_sentiment"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_published_at"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_deleted_at"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_content_hash"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_category"), table_name="rag_documents")
    op.drop_index("idx_rag_documents_source", table_name="rag_documents")
    op.drop_table("rag_documents")
