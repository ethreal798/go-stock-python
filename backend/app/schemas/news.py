"""多源财经快讯 API Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NewsSourceResponse(BaseModel):
    """数据源响应结果"""
    code: str = Field(..., description="数据源代码")
    name: str = Field(..., description="数据源名称")


class NewsTopicResponse(BaseModel):
    """快讯主题响应结果"""
    name: str


class NewsEntityResponse(BaseModel):
    """资讯关联实体 如股票、基金"""
    type: str
    name: str
    symbol: str


class NewsRelationResponse(BaseModel):
    """资讯原文链接"""
    url: str


class NewsItemResponse(BaseModel):
    """一条资讯 完整的响应字段"""
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
    """游标分页相关字段"""
    cursor_time: datetime
    cursor_id: int


####################################
# 响应结果  组装版
####################################
class NewsListResponse(BaseModel):
    """资讯列表响应结果字段"""
    items: list[NewsItemResponse]
    next_cursor: Optional[NewsCursorResponse] = None
    sync_id: int
    has_more: bool = False


class NewsUpdatesResponse(BaseModel):
    """"""
    items: list[NewsItemResponse]
    sync_id: int
    has_more: bool = False


class NewsTopicCountResponse(BaseModel):
    """资讯主题统计"""
    name: str
    news_count: int


class NewsOverviewResponse(BaseModel):
    """资讯不同源整体情况概览"""
    total_count: int
    important_count: int
    top_topics: list[NewsTopicCountResponse] = Field(default_factory=list)
