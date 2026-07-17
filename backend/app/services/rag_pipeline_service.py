"""RAG pipeline orchestration service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.news_ingest_service import NewsIngestService


class RagPipelineService:
    """Run RAG ingestion stages in order while preserving per-stage stats."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.news_ingest_service = NewsIngestService(db)
        self.chunk_service = ChunkService(db)
        self.embedding_service = EmbeddingService(db)

    async def run_news_pipeline(
        self,
        *,
        news_limit: int = 100,
        news_type: str = "all",
        relevant_only: bool = True,
        chunk_limit: int = 100,
        max_chars: int = 800,
        overlap_chars: int = 120,
        embed_limit: int = 100,
        embedding_model: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": False,
            "failed_stage": None,
            "error": None,
            "ingest": None,
            "chunk": None,
            "embed": None,
        }

        try:
            result["ingest"] = await self.news_ingest_service.ingest_telegraphs(
                limit=news_limit,
                news_type=news_type,
                relevant_only=relevant_only,
            )
        except Exception as exc:
            await self.db.rollback()
            return self._mark_failed(result, "ingest", exc)

        try:
            result["chunk"] = await self.chunk_service.chunk_pending_documents(
                limit=chunk_limit,
                max_chars=max_chars,
                overlap_chars=overlap_chars,
            )
        except Exception as exc:
            await self.db.rollback()
            return self._mark_failed(result, "chunk", exc)

        try:
            result["embed"] = await self.embedding_service.embed_pending_chunks(
                limit=embed_limit,
                model=embedding_model,
            )
        except Exception as exc:
            await self.db.rollback()
            return self._mark_failed(result, "embed", exc)

        result["success"] = True
        return result

    @staticmethod
    def _mark_failed(result: dict[str, Any], stage: str, exc: Exception) -> dict[str, Any]:
        result["failed_stage"] = stage
        result["error"] = str(exc)
        return result
