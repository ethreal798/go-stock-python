"""新闻资讯服务。

负责从财联社、华尔街见闻、新浪财经等源获取快讯。
"""

import logging

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Telegraph, Tags, TelegraphTags
from app.schemas.news import TelegraphResponse

logger = logging.getLogger(__name__)


class NewsService:
    """新闻资讯服务"""

    CLS_URL = "https://www.cls.cn/nodeapi/telegraphList"
    WSCN_URL = "https://api-one-wscn.awtmt.com/apiv1/content/lives"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_telegraphs(
            self,
            source: str = "cls",
            limit: int = 20,
            page: int = 1
    ) -> list[TelegraphResponse]:
        """获取电报快讯。

        如果数据库中有足够的数据，则直接返回；
        否则（或定时任务触发时）从远程接口抓取并存库。
        """

        # 1. 优先从数据库查询
        source_name = "财联社电报" if source == "cls" else "华尔街见闻"
        stmt = select(Telegraph).where(Telegraph.source.contains(source_name))
        stmt = stmt.order_by(desc(Telegraph.data_time)).limit(limit).offset((page - 1) * limit)

        result = await self.db.execute(stmt)
        telegraphs = result.scalars().all()

        if not telegraphs and page == 1:
            # 如果第一页没数据，主动触发数据
            await self.fetch_remote_news(source)
            # 重新查询
            result = await self.db.execute(stmt)
            telegraphs = result.scalars().all()

        return [
            TelegraphResponse(
                id=t.id,
                time=t.time,
                data_time=t.data_time,
                title=t.title,
                content=t.content,
                is_red=t.is_red,
                url=t.url,
                source=t.source,
                sentiment_result=t.sentiment_result,
                subjects=[],  # TODO：加载标签
                stocks=[]
            )
            for t in telegraphs
        ]

    # TODO
    async def fetch_remote_news(self, source: str = "cls") -> int:
        """从远程接口抓取最新新闻并入库。"""
