"""多源财经快讯模型。"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base


class NewsSource(Base):
    """稳定的数据来源字典；抓取配置仍由代码管理。"""

    __tablename__ = "news_sources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, comment="cls/wscn/sina")
    name = Column(String(100), nullable=False, comment="来源展示名称")
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    raw_items = relationship("NewsRawItem", back_populates="source")
    news_items = relationship("NewsItem", back_populates="source")

    __table_args__ = (UniqueConstraint("code", name="uq_news_sources_code"),)


class NewsRawItem(Base):
    """来源首次返回的单条快讯原始 JSON。"""

    __tablename__ = "news_raw_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_id = Column(BigInteger, ForeignKey("news_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_item_id = Column(String(128), nullable=False, comment="来源响应中的快讯 ID")
    payload = Column(JSONB, nullable=False, comment="单条快讯完整原始 JSON")
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())

    source = relationship("NewsSource", back_populates="raw_items")
    news_item = relationship("NewsItem", back_populates="raw_item", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_id", "source_item_id", name="uq_news_raw_source_item"),
        Index("ix_news_raw_source_published", "source_id", "published_at"),
    )


class NewsItem(Base):
    """跨来源统一的快讯/新闻主表。"""

    __tablename__ = "news_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    raw_item_id = Column(BigInteger, ForeignKey("news_raw_items.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(BigInteger, ForeignKey("news_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    content_type = Column(String(32), nullable=False, default="flash", server_default="flash", index=True)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    content_text = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)
    content_more_text = Column(Text, nullable=True)
    canonical_url = Column(String(1000), nullable=True)
    original_url = Column(String(1000), nullable=True)
    author_name = Column(String(200), nullable=True)
    source_importance_code = Column(String(32), nullable=True)
    is_source_important = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    is_pinned = Column(Boolean, nullable=False, default=False, server_default="false")
    is_focus = Column(Boolean, nullable=False, default=False, server_default="false")
    is_calendar = Column(Boolean, nullable=False, default=False, server_default="false")
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    raw_item = relationship("NewsRawItem", back_populates="news_item")
    source = relationship("NewsSource", back_populates="news_items")
    topics = relationship("NewsItemTopic", back_populates="news_item", cascade="all, delete-orphan", lazy="selectin")
    entities = relationship("NewsItemEntity", back_populates="news_item", cascade="all, delete-orphan", lazy="selectin")
    relations = relationship(
        "NewsItemRelation", back_populates="news_item", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("raw_item_id", name="uq_news_items_raw_item_id"),
        Index("ix_news_items_type_published", "content_type", "published_at", "id"),
        Index("ix_news_items_source_published", "source_id", "published_at", "id"),
        Index("ix_news_items_important_published", "is_source_important", "published_at"),
    )


class NewsItemTopic(Base):
    """来源提供的频道、主题或标签。"""

    __tablename__ = "news_item_topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_item_id = Column(BigInteger, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_type = Column(String(32), nullable=False, index=True, comment="channel/subject/theme/tag")
    source_topic_id = Column(String(128), nullable=True)
    code = Column(String(128), nullable=True)
    name = Column(String(200), nullable=False, index=True)
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())

    news_item = relationship("NewsItem", back_populates="topics")

    __table_args__ = (
        UniqueConstraint("news_item_id", "topic_type", "name", name="uq_news_item_topic"),
        Index("ix_news_topics_type_name", "topic_type", "name"),
    )


class NewsItemEntity(Base):
    """来源直接给出的股票、基金、外汇等关联标的。"""

    __tablename__ = "news_item_entities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_item_id = Column(BigInteger, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(32), nullable=False, index=True)
    market = Column(String(32), nullable=True, index=True)
    source_symbol = Column(String(100), nullable=True)
    normalized_symbol = Column(String(100), nullable=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    price_at_publish = Column(Numeric(20, 6), nullable=True)
    change_pct_at_publish = Column(Numeric(12, 6), nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())

    news_item = relationship("NewsItem", back_populates="entities")

    __table_args__ = (
        UniqueConstraint("news_item_id", "entity_type", "source_symbol", name="uq_news_item_entity"),
        Index("ix_news_entities_normalized_type", "normalized_symbol", "entity_type"),
    )


class NewsItemRelation(Base):
    """公告原文、相关文章和关联事实。"""

    __tablename__ = "news_item_relations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_item_id = Column(BigInteger, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(32), nullable=False, index=True)
    source_related_id = Column(String(128), nullable=True)
    title = Column(String(500), nullable=True)
    url = Column(String(1500), nullable=True)
    content = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())

    news_item = relationship("NewsItem", back_populates="relations")

    __table_args__ = (
        UniqueConstraint("news_item_id", "relation_type", "source_related_id", "url", name="uq_news_item_relation"),
    )
