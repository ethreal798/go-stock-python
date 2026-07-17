"""AI RAG 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.rag import (
    RagChunkBatchResponse,
    RagChunkRequest,
    RagChunkResponse,
    RagDocumentResponse,
    RagEmbedRequest,
    RagEmbedResponse,
    RagNewsIngestRequest,
    RagNewsIngestResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
)
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.news_ingest_service import NewsIngestService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/ai/rag", tags=["ai-rag"])


def get_news_ingest_service(db: AsyncSession = Depends(get_db)) -> NewsIngestService:
    return NewsIngestService(db)


def get_chunk_service(db: AsyncSession = Depends(get_db)) -> ChunkService:
    return ChunkService(db)


def get_embedding_service(db: AsyncSession = Depends(get_db)) -> EmbeddingService:
    return EmbeddingService(db)


def get_retrieval_service(db: AsyncSession = Depends(get_db)) -> RetrievalService:
    return RetrievalService(db)


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


@router.post("/chunk", response_model=RagChunkBatchResponse, summary="将 RAG 文档切分为 chunk")
async def chunk_documents(
    request: RagChunkRequest,
    service: ChunkService = Depends(get_chunk_service),
) -> RagChunkBatchResponse:
    stats = await service.chunk_pending_documents(
        limit=request.limit,
        max_chars=request.max_chars,
        overlap_chars=request.overlap_chars,
    )
    return RagChunkBatchResponse(success=True, **stats)


@router.get("/chunks", response_model=list[RagChunkResponse], summary="查看最新 RAG chunk")
async def list_chunks(
    limit: int = Query(20, ge=1, le=100),
    service: ChunkService = Depends(get_chunk_service),
) -> list[RagChunkResponse]:
    chunks = await service.list_chunks(limit=limit)
    return [RagChunkResponse.model_validate(chunk) for chunk in chunks]


@router.post("/embed", response_model=RagEmbedResponse, summary="将 RAG chunk 向量化")
async def embed_chunks(
    request: RagEmbedRequest,
    service: EmbeddingService = Depends(get_embedding_service),
) -> RagEmbedResponse:
    stats = await service.embed_pending_chunks(limit=request.limit, model=request.model)
    return RagEmbedResponse(success=True, **stats)


@router.post("/retrieve", response_model=RagRetrieveResponse, summary="检索 RAG chunk")
async def retrieve_chunks(
    request: RagRetrieveRequest,
    service: RetrievalService = Depends(get_retrieval_service),
) -> RagRetrieveResponse:
    result = await service.retrieve(
        query=request.query,
        top_k=request.top_k,
        days=request.days,
        model=request.model,
        use_vector=request.use_vector,
    )
    return RagRetrieveResponse.model_validate(result)
