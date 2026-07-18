"""RAG 检索服务。"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.rag import RagChunk, RagChunkEmbedding
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """RAG chunk 召回服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.embedding_service = EmbeddingService(db)

    async def retrieve(
        self,
        query: str,
        top_k: int = 8,
        days: int | None = 7,
        model: str | None = None,
        use_vector: bool = True,
    ) -> dict[str, Any]:
        """混合召回 RAG chunk。"""
        embedding_model = model or settings.AI_EMBEDDING_MODEL
        candidates: dict[int, dict[str, Any]] = {}

        if use_vector:
            try:
                vector_items = await self._vector_retrieve(
                    query=query,
                    top_k=top_k,
                    days=days,
                    model=embedding_model,
                )
                self._merge_candidates(candidates, vector_items)
            except Exception as exc:
                logger.warning("Vector retrieval failed, fallback to keyword retrieval: %s", exc)

        keyword_items = await self._keyword_retrieve(query=query, top_k=top_k, days=days)
        self._merge_candidates(candidates, keyword_items)

        if not candidates:
            latest_items = await self._latest_retrieve(top_k=top_k, days=days)
            self._merge_candidates(candidates, latest_items)

        items = sorted(candidates.values(), key=lambda item: item["score"], reverse=True)[:top_k]

        return {
            "query": query,
            "top_k": top_k,
            "days": days,
            "model": embedding_model,
            "items": [self._format_item(item) for item in items],
        }

    async def _vector_retrieve(
        self,
        query: str,
        top_k: int,
        days: int | None,
        model: str,
    ) -> list[dict[str, Any]]:
        query_vector = (await self.embedding_service.embed_texts([query], model=model))[0]
        distance = RagChunkEmbedding.embedding_vector.cosine_distance(query_vector).label("distance")
        join_condition = and_(
            RagChunkEmbedding.chunk_id == RagChunk.id,
            RagChunkEmbedding.embedding_model == model,
        )
        stmt = (
            select(RagChunk, distance).join(RagChunkEmbedding, join_condition).order_by(distance.asc()).limit(top_k * 3)
        )
        stmt = self._apply_time_filter(stmt, days)

        result = await self.db.execute(stmt)
        items: list[dict[str, Any]] = []
        for chunk, vector_distance in result.all():
            score = max(0.0, 1.0 - float(vector_distance or 0))
            items.append({"chunk": chunk, "score": score, "match_type": "vector"})
        return items

    async def _keyword_retrieve(self, query: str, top_k: int, days: int | None) -> list[dict[str, Any]]:
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        conditions = [RagChunk.chunk_text.ilike(f"%{keyword}%") for keyword in keywords]
        stmt = (
            select(RagChunk)
            .where(or_(*conditions))
            .order_by(desc(RagChunk.importance_score), desc(RagChunk.published_at), desc(RagChunk.id))
            .limit(top_k * 3)
        )
        stmt = self._apply_time_filter(stmt, days)

        result = await self.db.execute(stmt)
        items: list[dict[str, Any]] = []
        for chunk in result.scalars().all():
            score = self._keyword_score(chunk.chunk_text, keywords, chunk.importance_score or 0)
            items.append({"chunk": chunk, "score": score, "match_type": "keyword"})
        return items

    async def _latest_retrieve(self, top_k: int, days: int | None) -> list[dict[str, Any]]:
        stmt = select(RagChunk).order_by(desc(RagChunk.published_at), desc(RagChunk.id)).limit(top_k)
        stmt = self._apply_time_filter(stmt, days)

        result = await self.db.execute(stmt)
        return [
            {"chunk": chunk, "score": 0.1 + min((chunk.importance_score or 0) / 1000, 0.1), "match_type": "latest"}
            for chunk in result.scalars().all()
        ]

    def _apply_time_filter(self, stmt, days: int | None):
        if not days:
            return stmt

        since = datetime.now() - timedelta(days=days)
        return stmt.where(or_(RagChunk.published_at >= since, RagChunk.published_at.is_(None)))

    def _merge_candidates(self, candidates: dict[int, dict[str, Any]], items: list[dict[str, Any]]) -> None:
        for item in items:
            chunk = item["chunk"]
            existing = candidates.get(chunk.id)
            if existing is None or item["score"] > existing["score"]:
                candidates[chunk.id] = item
            elif item["match_type"] not in existing["match_type"]:
                existing["match_type"] = f"{existing['match_type']}+{item['match_type']}"

    def _format_item(self, item: dict[str, Any]) -> dict[str, Any]:
        chunk: RagChunk = item["chunk"]
        metadata = chunk.extra_metadata or {}
        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "title": metadata.get("document_title"),
            "content": chunk.chunk_text,
            "source_name": chunk.source_name,
            "url": metadata.get("document_url"),
            "published_at": chunk.published_at,
            "category": chunk.category,
            "sentiment": chunk.sentiment,
            "score": round(float(item["score"]), 6),
            "match_type": item["match_type"],
        }

    def _extract_keywords(self, query: str) -> list[str]:
        cleaned = re.sub(r"[，。！？、；：,.!?;:\s]+", " ", query).strip()
        words = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_\-]{2,}", cleaned)

        keywords: list[str] = []
        if 2 <= len(cleaned) <= 30:
            keywords.append(cleaned)

        for word in words:
            if word not in keywords:
                keywords.append(word)

        return keywords[:8]

    @staticmethod
    def _keyword_score(text: str, keywords: list[str], importance_score: int) -> float:
        matched = sum(1 for keyword in keywords if keyword in text)
        base_score = min(0.8, matched * 0.2)
        importance_bonus = min(importance_score / 1000, 0.1)
        return base_score + importance_bonus
