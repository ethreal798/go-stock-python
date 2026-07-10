"""新闻资讯相关 Pydantic Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelegraphResponse(BaseModel):
    """电报/快讯响应。"""

    id: Optional[int] = None
    time: str = Field(..., description="时间，如 15:04:05")
    data_time: Optional[datetime] = Field(None, description="完整数据时间")
    title: Optional[str] = Field(None, description="标题")
    content: str = Field(..., description="正文内容")
    is_red: bool = Field(False, description="是否加红/重要")
    url: Optional[str] = Field(None, description="原文链接")
    source: str = Field(..., description="来源，如 财联社、华尔街见闻")
    sentiment_result: Optional[str] = Field(None, description="情感分析结果")
    subjects: list[str] = Field(default_factory=list, description="相关板块/主题")
    stocks: list[str] = Field(default_factory=list, description="相关股票")

    # 新增字段
    is_relevant: bool = Field(True, description="是否为金融相关新闻")
    relevance_score: int = Field(0, description="相关性评分 0-100")
    category: Optional[str] = Field(None, description="新闻分类")

    model_config = {"from_attributes": True}
