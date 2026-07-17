"""RAG chunk 向量化服务。"""

import logging

import httpx
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.rag import RagChunk, RagChunkEmbedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    """调用 OpenAI 兼容接口生成 embedding 并写入 pgvector。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def embed_pending_chunks(self, limit: int = 100, model: str | None = None) -> dict[str, int | str]:
        """向量化尚未使用指定模型处理过的 chunk。"""
        embedding_model = model or settings.AI_EMBEDDING_MODEL
        chunks = await self._get_chunks_without_embedding(limit=limit, model=embedding_model)
        stats: dict[str, int | str] = {
            "scanned": len(chunks),
            "embedded": 0,
            "skipped_existing": 0,
            "skipped_invalid": 0,
            "model": embedding_model,
            "embedding_dim": settings.AI_EMBEDDING_DIM,
        }

        if not chunks:
            return stats

        batch_size = max(1, settings.AI_EMBEDDING_BATCH_SIZE)
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            inputs = [chunk.chunk_text for chunk in batch if chunk.chunk_text and chunk.chunk_text.strip()]
            valid_chunks = [chunk for chunk in batch if chunk.chunk_text and chunk.chunk_text.strip()]

            invalid_count = len(batch) - len(valid_chunks)
            if invalid_count:
                stats["skipped_invalid"] = int(stats["skipped_invalid"]) + invalid_count

            if not valid_chunks:
                continue

            vectors = await self.embed_texts(inputs, model=embedding_model)
            for chunk, vector in zip(valid_chunks, vectors):
                self.db.add(
                    RagChunkEmbedding(
                        chunk_id=chunk.id,
                        embedding_model=embedding_model,
                        embedding_dim=len(vector),
                        embedding_vector=vector,
                    )
                )
                stats["embedded"] = int(stats["embedded"]) + 1

        if int(stats["embedded"]) > 0:
            await self.db.commit()

        return stats

    async def embed_texts(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """调用 OpenAI 兼容 /embeddings 接口。"""
        if not texts:
            return []

        embedding_model = model or settings.AI_EMBEDDING_MODEL
        payload = {"model": embedding_model, "input": texts}
        headers = {"Content-Type": "application/json"}

        api_key = settings.AI_EMBEDDING_API_KEY or settings.AI_API_KEY
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{settings.AI_EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        vectors = [item["embedding"] for item in sorted(data.get("data", []), key=lambda item: item.get("index", 0))]
        self._validate_vectors(vectors, expected_count=len(texts))
        return vectors

    async def _get_chunks_without_embedding(self, limit: int, model: str) -> list[RagChunk]:
        join_condition = and_(
            RagChunkEmbedding.chunk_id == RagChunk.id,
            RagChunkEmbedding.embedding_model == model,
        )
        stmt = (
            select(RagChunk)
            .outerjoin(RagChunkEmbedding, join_condition)
            .where(RagChunkEmbedding.id.is_(None))
            .order_by(desc(RagChunk.published_at), desc(RagChunk.id))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _validate_vectors(self, vectors: list[list[float]], expected_count: int) -> None:
        if len(vectors) != expected_count:
            raise ValueError(f"Embedding result count mismatch: expected {expected_count}, got {len(vectors)}")

        for index, vector in enumerate(vectors):
            if len(vector) != settings.AI_EMBEDDING_DIM:
                raise ValueError(
                    f"Embedding dimension mismatch at index {index}: "
                    f"expected {settings.AI_EMBEDDING_DIM}, got {len(vector)}"
                )
