"""统一资讯主表进入 RAG 文档表的服务。"""

import hashlib
from datetime import timezone
from typing import Any

from sqlalchemy import Select, and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.news import NewsItem
from app.models.rag import RagDocument


class NewsIngestService:
    """将尚未同步的 NewsItem 写入 RAG 文档表。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest_telegraphs(
        self, limit: int = 100, news_type: str = "all", relevant_only: bool = True
    ) -> dict[str, int]:
        """方法名保留 API 兼容；V1 没有相关性分析，relevant_only 暂不参与过滤。"""
        del relevant_only
        stmt = self._build_news_query(limit=limit, news_type=news_type)
        result = await self.db.execute(stmt)
        news_items = list(result.scalars().unique().all())

        stats = {"scanned": len(news_items), "ingested": 0, "skipped_invalid": 0}
        for item in news_items:
            if not item.content or not item.content.strip():
                stats["skipped_invalid"] += 1
                continue
            self.db.add(self._build_document(item))
            stats["ingested"] += 1

        if stats["ingested"]:
            await self.db.commit()
        return stats

    async def list_documents(self, limit: int = 20) -> list[RagDocument]:
        result = await self.db.execute(select(RagDocument).order_by(desc(RagDocument.created_at)).limit(limit))
        return list(result.scalars().all())

    def _build_news_query(self, limit: int, news_type: str) -> Select[tuple[NewsItem]]:
        stmt = select(NewsItem).options(
            selectinload(NewsItem.source),
            selectinload(NewsItem.topics),
            selectinload(NewsItem.entities),
            selectinload(NewsItem.relations),
        )

        normalized_type = {"fast": "flash", "news": "article"}.get(news_type, news_type)
        if normalized_type != "all":
            stmt = stmt.where(NewsItem.content_type == normalized_type)

        existing_document = (
            select(RagDocument.source_id)
            .where(
                and_(
                    RagDocument.source_type == NewsItem.content_type,
                    RagDocument.source_id == NewsItem.id,
                )
            )
            .exists()
        )
        return (
            stmt.where(~existing_document, NewsItem.content.is_not(None), NewsItem.content != "")
            .order_by(desc(NewsItem.published_at), desc(NewsItem.id))
            .limit(limit)
        )

    def _build_document(self, item: NewsItem) -> RagDocument:
        content = item.content.strip()

        return RagDocument(
            source_type=item.content_type,
            source_id=item.id,
            title=(item.title or "").strip() or None,
            content=content,
            content_hash=self._hash_text(content),
            published_at=self._rag_datetime(item.published_at),
            source_name=item.source.name,
            url=self._original_document_url(item),
            category=None,
            importance_score=100 if item.is_source_important else 0,
            sentiment=None,
            language="zh",
            status="pending",
            extra_metadata=self._build_metadata(item),
        )

    @staticmethod
    def _build_metadata(item: NewsItem) -> dict[str, Any]:
        return {
            "source_code": item.source.code,
            "is_source_important": bool(item.is_source_important),
            "topics": [topic.name for topic in item.topics],
            "entities": [
                {
                    "type": entity.entity_type,
                    "name": entity.name,
                    "symbol": entity.symbol,
                }
                for entity in item.entities
            ],
        }

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _original_document_url(item: NewsItem) -> str | None:
        return next((relation.url for relation in item.relations if relation.url), None)

    @staticmethod
    def _rag_datetime(value):
        """旧 RAG 时间列不带时区，统一写入 UTC naive 值。"""
        if value is None or value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
