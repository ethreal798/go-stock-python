"""RAG 相关模型。"""

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, GormBaseModel


class RagDocument(GormBaseModel):
    """统一的 RAG 文档主表。"""

    __tablename__ = "rag_documents"

    source_type = Column(String(50), index=True, nullable=False, comment="来源类型: telegraph/news/notice/report")
    source_id = Column(BigInteger, index=True, nullable=False, comment="来源记录ID")
    title = Column(String(500), nullable=True, comment="文档标题")
    content = Column(Text, nullable=False, comment="文档正文")
    content_hash = Column(String(64), index=True, nullable=False, comment="正文哈希")
    summary = Column(Text, nullable=True, comment="预生成摘要")
    published_at = Column(DateTime, index=True, nullable=True, comment="发布时间")
    source_name = Column(String(100), index=True, nullable=True, comment="来源名称")
    url = Column(String(500), nullable=True, comment="原文链接")
    category = Column(String(50), index=True, nullable=True, comment="新闻分类")
    importance_score = Column(Integer, default=0, server_default="0", comment="重要性评分")
    sentiment = Column(String(50), index=True, nullable=True, comment="情绪标签")
    language = Column(String(20), default="zh", server_default="zh", comment="语言")
    status = Column(String(20), default="pending", server_default="pending", index=True, comment="处理状态")
    extra_metadata = Column(JSON, nullable=True, comment="扩展元数据")

    chunks = relationship("RagChunk", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("RagEntity", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_rag_documents_source", "source_type", "source_id"),
    )


class RagChunk(GormBaseModel):
    """RAG 检索分块。"""

    __tablename__ = "rag_chunks"

    document_id = Column(BigInteger, ForeignKey("rag_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False, comment="文档内块序号")
    chunk_text = Column(Text, nullable=False, comment="分块内容")
    chunk_hash = Column(String(64), index=True, nullable=False, comment="分块哈希")
    token_count = Column(Integer, default=0, server_default="0", comment="估算 token 数")
    start_offset = Column(Integer, default=0, server_default="0")
    end_offset = Column(Integer, default=0, server_default="0")
    published_at = Column(DateTime, index=True, nullable=True)
    source_name = Column(String(100), index=True, nullable=True)
    category = Column(String(50), index=True, nullable=True)
    importance_score = Column(Integer, default=0, server_default="0")
    sentiment = Column(String(50), index=True, nullable=True)
    extra_metadata = Column(JSON, nullable=True, comment="块级元数据")

    document = relationship("RagDocument", back_populates="chunks")
    embeddings = relationship("RagChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan")
    entities = relationship("RagEntity", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_rag_chunks_doc_chunk", "document_id", "chunk_index", unique=True),
    )


class RagChunkEmbedding(Base):
    """RAG 分块向量。"""

    __tablename__ = "rag_chunk_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chunk_id = Column(BigInteger, ForeignKey("rag_chunks.id", ondelete="CASCADE"), index=True, nullable=False)
    embedding_model = Column(String(100), index=True, nullable=False)
    embedding_dim = Column(Integer, nullable=False)
    embedding_vector = Column(Vector(1024), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    chunk = relationship("RagChunk", back_populates="embeddings")

    __table_args__ = (
        Index("idx_rag_chunk_embeddings_chunk_model", "chunk_id", "embedding_model", unique=True),
    )


class RagEntity(GormBaseModel):
    """RAG 文档/分块实体抽取结果。"""

    __tablename__ = "rag_entities"

    document_id = Column(BigInteger, ForeignKey("rag_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_id = Column(BigInteger, ForeignKey("rag_chunks.id", ondelete="CASCADE"), index=True, nullable=True)
    entity_type = Column(String(50), index=True, nullable=False, comment="stock/industry/concept/macro/person/org")
    entity_name = Column(String(200), index=True, nullable=False)
    entity_code = Column(String(50), index=True, nullable=True)
    alias = Column(String(200), nullable=True)
    weight = Column(Float, default=0, server_default="0", comment="实体权重")
    extra_metadata = Column(JSON, nullable=True)

    document = relationship("RagDocument", back_populates="entities")
    chunk = relationship("RagChunk", back_populates="entities")

    __table_args__ = (
        Index("idx_rag_entities_type_name", "entity_type", "entity_name"),
    )


class RagQueryLog(Base):
    """RAG 查询日志。"""

    __tablename__ = "rag_query_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), index=True, nullable=True)
    user_query = Column(Text, nullable=False)
    query_intent = Column(String(50), index=True, nullable=True)
    query_filters = Column(JSON, nullable=True)
    retrieved_chunk_ids = Column(JSON, nullable=True)
    model_name = Column(String(100), index=True, nullable=True)
    answer = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True, nullable=False)
