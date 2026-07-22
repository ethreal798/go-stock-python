"""RAG chunk 向量化服务。"""

import asyncio
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

            await self.db.commit()

        return stats

    # 调用Embedding模型进行向量化
    async def embed_texts(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """调用 OpenAI 兼容 /embeddings 接口。"""
        if not texts:
            return []

        embedding_model = model or settings.AI_EMBEDDING_MODEL
        payload = {"model": embedding_model, "input": texts}
        if settings.AI_EMBEDDING_REQUEST_DIMENSIONS > 0:
            payload["dimensions"] = settings.AI_EMBEDDING_REQUEST_DIMENSIONS
        headers = {"Content-Type": "application/json"}

        api_key = settings.AI_EMBEDDING_API_KEY or settings.AI_API_KEY
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{settings.AI_EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
        async with httpx.AsyncClient(timeout=float(settings.AI_EMBEDDING_TIMEOUT_SECONDS)) as client:
            response = await self._post_with_retry(client, url, payload, headers)

        data = response.json()
        vectors = [item["embedding"] for item in sorted(data.get("data", []), key=lambda item: item.get("index", 0))]
        self._validate_vectors(vectors, expected_count=len(texts))
        return vectors

    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: dict,
        headers: dict[str, str],
    ) -> httpx.Response:
        retryable_status_codes = {408, 409, 425, 429, 500, 502, 503, 504}
        max_retries = max(0, settings.AI_EMBEDDING_MAX_RETRIES)

        for attempt in range(max_retries + 1):
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code not in retryable_status_codes:
                    self._raise_for_embedding_error(response, url)
                    return response

                if attempt >= max_retries:
                    self._raise_for_embedding_error(response, url)
                    return response

                await asyncio.sleep(self._retry_delay_seconds(response, attempt))
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError):
                if attempt >= max_retries:
                    raise
                await asyncio.sleep(self._retry_delay_seconds(None, attempt))

        raise RuntimeError("Embedding request retry loop exited unexpectedly")

    @staticmethod
    def _raise_for_embedding_error(response: httpx.Response, url: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = response.text[:1000]
            raise httpx.HTTPStatusError(
                f"{exc}. Provider response body: {body}. Request URL: {url}",
                request=exc.request,
                response=exc.response,
            ) from exc

    def _retry_delay_seconds(self, response: httpx.Response | None, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                logger.warning("Ignore unsupported Retry-After header: %s", retry_after)

        return settings.AI_EMBEDDING_RETRY_BASE_SECONDS * (2**attempt)

    # 过滤已向量化的切片文档
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
