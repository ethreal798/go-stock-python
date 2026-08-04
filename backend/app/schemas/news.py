"""多源财经快讯 API Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NewsSourceResponse(BaseModel):
    code: str
    name: str


class NewsTopicResponse(BaseModel):
    name: str


class NewsEntityResponse(BaseModel):
    type: str
    name: str
    symbol: str


class NewsRelationResponse(BaseModel):
    url: str


class NewsItemResponse(BaseModel):
    id: int
    source: NewsSourceResponse
    content_type: str
    title: Optional[str] = None
    content: str
    is_source_important: bool
    published_at: datetime
    topics: list[NewsTopicResponse] = Field(default_factory=list)
    entities: list[NewsEntityResponse] = Field(default_factory=list)
    relations: list[NewsRelationResponse] = Field(default_factory=list)


class NewsCursorResponse(BaseModel):
    time: datetime
    id: int


class NewsListResponse(BaseModel):
    items: list[NewsItemResponse]
    next_cursor: Optional[NewsCursorResponse] = None
    has_more: bool = False


class NewsTopicCountResponse(BaseModel):
    name: str
    news_count: int


class NewsOverviewResponse(BaseModel):
    total_count: int
    important_count: int
    top_topics: list[NewsTopicCountResponse] = Field(default_factory=list)
