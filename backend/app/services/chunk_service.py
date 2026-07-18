"""RAG 文档切块服务。"""

import hashlib
import re

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag import RagChunk, RagDocument


class ChunkService:
    """将 RAG 文档切分为可检索的 chunk。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def chunk_pending_documents(
        self,
        limit: int = 100,
        max_chars: int = 800,
        overlap_chars: int = 120,
    ) -> dict[str, int]:
        """切分 pending 状态的 RAG 文档。"""
        stmt = self._build_pending_documents_query(limit=limit)
        result = await self.db.execute(stmt)
        documents = result.scalars().all()

        stats = {
            "scanned": len(documents),
            "chunked_documents": 0,
            "chunks_created": 0,
            "skipped_existing": 0,
            "skipped_invalid": 0,
        }

        for document in documents:
            if await self._has_chunks(document.id):
                document.status = "chunked"
                stats["skipped_existing"] += 1
                continue

            chunks = self.split_document_text(document, max_chars=max_chars, overlap_chars=overlap_chars)
            if not chunks:
                document.status = "failed"
                stats["skipped_invalid"] += 1
                continue

            for index, chunk_data in enumerate(chunks):
                self.db.add(self._build_chunk(document, index, chunk_data))

            document.status = "chunked"
            stats["chunked_documents"] += 1
            stats["chunks_created"] += len(chunks)

        if stats["chunked_documents"] > 0 or stats["skipped_existing"] > 0 or stats["skipped_invalid"] > 0:
            await self.db.commit()

        return stats

    async def list_chunks(self, limit: int = 20) -> list[RagChunk]:
        """列出最新的 RAG 分块。"""
        stmt = select(RagChunk).order_by(desc(RagChunk.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def split_document_text(
        self,
        document: RagDocument,
        max_chars: int = 800,
        overlap_chars: int = 120,
    ) -> list[dict[str, int | str]]:
        """将文档正文切为带偏移量的文本块。"""
        text = self._build_text_for_chunking(document)
        if not text:
            return []

        if len(text) <= max_chars:
            return [{"text": text, "start": 0, "end": len(text)}]

        chunks: list[dict[str, int | str]] = []
        start = 0
        text_length = len(text)
        step = max(1, max_chars - overlap_chars)

        while start < text_length:
            end = min(start + max_chars, text_length)
            adjusted_end = self._find_sentence_boundary(text, start, end)
            chunk_text = text[start:adjusted_end].strip()

            if chunk_text:
                chunks.append({"text": chunk_text, "start": start, "end": adjusted_end})

            if adjusted_end >= text_length:
                break

            start = max(adjusted_end - overlap_chars, start + step)

        return chunks

    def _build_pending_documents_query(self, limit: int) -> Select[tuple[RagDocument]]:
        return (
            select(RagDocument)
            .where(RagDocument.status == "pending")
            .order_by(desc(RagDocument.published_at), desc(RagDocument.id))
            .limit(limit)
        )

    async def _has_chunks(self, document_id: int) -> bool:
        stmt = select(RagChunk.id).where(RagChunk.document_id == document_id).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _build_chunk(self, document: RagDocument, chunk_index: int, chunk_data: dict[str, int | str]) -> RagChunk:
        chunk_text = str(chunk_data["text"])
        return RagChunk(
            document_id=document.id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            chunk_hash=self._hash_text(chunk_text),
            token_count=self._estimate_token_count(chunk_text),
            start_offset=int(chunk_data["start"]),
            end_offset=int(chunk_data["end"]),
            published_at=document.published_at,
            source_name=document.source_name,
            category=document.category,
            importance_score=document.importance_score or 0,
            sentiment=document.sentiment,
            extra_metadata={
                "document_title": document.title,
                "document_url": document.url,
                "source_type": document.source_type,
                "source_id": document.source_id,
            },
        )

    def _build_text_for_chunking(self, document: RagDocument) -> str:
        title = self._normalize_text(document.title or "")
        content = self._normalize_text(document.content or "")

        if not content:
            return ""

        if title and title not in content:
            return f"标题：{title}\n正文：{content}"

        return content

    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        if end >= len(text):
            return len(text)

        window = text[start:end]
        matches = list(re.finditer(r"[。！？!?；;\n]", window))
        if not matches:
            return end

        boundary = start + matches[-1].end()
        min_reasonable_end = start + int((end - start) * 0.6)
        return boundary if boundary >= min_reasonable_end else end

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        non_chinese_words = len(re.findall(r"[A-Za-z0-9_]+", text))
        return chinese_chars + non_chinese_words

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
