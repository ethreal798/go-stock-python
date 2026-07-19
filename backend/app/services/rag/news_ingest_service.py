"""新闻入 RAG 主表服务。"""

import hashlib
from typing import Any

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Telegraph
from app.models.rag import RagDocument


class NewsIngestService:
    """将新闻主表同步到 RAG 文档表。"""

    SOURCE_TYPE = "telegraph"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest_telegraphs(
        self, limit: int = 100, news_type: str = "all", relevant_only: bool = True
    ) -> dict[str, int]:
        """将 telegraph_list 中的新闻同步到 rag_documents。"""
        # 根据请求参数初步筛选
        stmt = self._build_telegraph_query(limit=limit, news_type=news_type, relevant_only=relevant_only)
        result = await self.db.execute(stmt)
        telegraphs = result.scalars().all()

        stats = {
            "scanned": len(telegraphs),
            "ingested": 0,
            "skipped_invalid": 0,
        }

        for telegraph in telegraphs:
            # 过滤没有有效内容的资讯或新闻
            if not telegraph.content or not telegraph.content.strip():
                stats["skipped_invalid"] += 1
                continue

            # 将资讯或新闻入库
            document = self._build_document_from_telegraph(telegraph)
            self.db.add(document)
            stats["ingested"] += 1

        if stats["ingested"] > 0:
            await self.db.commit()

        return stats

    async def list_documents(self, limit: int = 20) -> list[RagDocument]:
        """列出最新的 RAG 文档。"""
        stmt = select(RagDocument).order_by(desc(RagDocument.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _build_telegraph_query(self, limit: int, news_type: str, relevant_only: bool) -> Select[tuple[Telegraph]]:
        stmt = select(Telegraph)

        if news_type != "all":
            stmt = stmt.where(Telegraph.type == news_type)

        if relevant_only:
            stmt = stmt.where(Telegraph.is_relevant == bool(1))

        existing_document = (
            select(RagDocument.source_id)
            .where(
                RagDocument.source_type == self.SOURCE_TYPE,
                RagDocument.source_id == Telegraph.id,
            )
            .exists()
        )

        stmt = stmt.where(
            ~existing_document,
            Telegraph.content.is_not(None),
            Telegraph.content != "",
        )

        return stmt.order_by(desc(Telegraph.data_time), desc(Telegraph.id)).limit(limit)

    def _build_document_from_telegraph(self, telegraph: Telegraph) -> RagDocument:
        content = telegraph.content.strip()
        title = (telegraph.title or "").strip() or None

        return RagDocument(
            source_type=self.SOURCE_TYPE,
            source_id=telegraph.id,
            title=title,
            content=content,
            content_hash=self._hash_text(content),
            published_at=telegraph.data_time,
            source_name=telegraph.source,
            url=telegraph.url,
            category=telegraph.category,
            importance_score=int(telegraph.relevance_score or 0),
            sentiment=telegraph.sentiment_result,
            language="zh",
            status="pending",
            extra_metadata=self._build_metadata(telegraph),
        )

    def _build_metadata(self, telegraph: Telegraph) -> dict[str, Any]:
        return {
            "time": telegraph.time,
            "is_red": bool(telegraph.is_red),
            "type": telegraph.type,
            "is_relevant": bool(telegraph.is_relevant),
            "relevance_score": int(telegraph.relevance_score or 0),
        }

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
