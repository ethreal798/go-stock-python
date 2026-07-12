"""RAG 相关 Pydantic Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RagDocumentResponse(BaseModel):
    """RAG 文档响应。"""

    id: int
    source_type: str
    source_id: int
    title: Optional[str] = None
    content: str
    content_hash: str
    published_at: Optional[datetime] = None
    source_name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    importance_score: int = 0
    sentiment: Optional[str] = None
    language: str = "zh"
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RagNewsIngestRequest(BaseModel):
    """新闻入库请求。"""

    limit: int = Field(100, ge=1, le=1000, description="本次最多处理多少条新闻")
    news_type: str = Field("all", description="新闻类型: all / fast / news")
    relevant_only: bool = Field(True, description="是否仅处理金融相关资讯")


class RagNewsIngestResponse(BaseModel):
    """新闻入库响应。"""

    success: bool = True
    scanned: int = 0
    ingested: int = 0
    skipped_existing: int = 0
    skipped_invalid: int = 0
