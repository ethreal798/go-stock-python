"""AI RAG 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.rag import (
    RagDocumentResponse,
    RagNewsIngestRequest,
    RagNewsIngestResponse,
)
from app.services.news_ingest_service import NewsIngestService

router = APIRouter(prefix="/ai/rag", tags=["ai-rag"])


def get_news_ingest_service(db: AsyncSession = Depends(get_db)) -> NewsIngestService:
    return NewsIngestService(db)


@router.post("/ingest/news", response_model=RagNewsIngestResponse, summary="将新闻同步到 RAG 文档表")
async def ingest_news(
    request: RagNewsIngestRequest,
    service: NewsIngestService = Depends(get_news_ingest_service),
) -> RagNewsIngestResponse:
    stats = await service.ingest_telegraphs(
        limit=request.limit,
        news_type=request.news_type,
        relevant_only=request.relevant_only,
    )
    return RagNewsIngestResponse(success=True, **stats)


@router.get("/documents", response_model=list[RagDocumentResponse], summary="查看最新 RAG 文档")
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    service: NewsIngestService = Depends(get_news_ingest_service),
) -> list[RagDocumentResponse]:
    documents = await service.list_documents(limit=limit)
    return [RagDocumentResponse.model_validate(document) for document in documents]
