"""多源财经快讯查询服务。"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, desc, distinct, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.news import (
    NewsItem,
    NewsItemTopic,
    NewsSource,
)
from app.schemas.news import (
    NewsCursorResponse,
    NewsEntityResponse,
    NewsItemResponse,
    NewsListResponse,
    NewsOverviewResponse,
    NewsRelationResponse,
    NewsSourceResponse,
    NewsTopicCountResponse,
    NewsTopicResponse,
    NewsUpdatesResponse,
)
from app.services.news import NewsCrawler

logger = logging.getLogger(__name__)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
GENERIC_TOPIC_NAMES = {"其他", "全球", "7x24快讯", "7×24快讯", "选股宝"}


class NewsService:
    """快讯的后端统一入口（查询 + 抓取调度）。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._crawler = NewsCrawler(db)

    # ------------------------------------------------------------------
    # 采集与入库（委托给 NewsCrawler）
    # ------------------------------------------------------------------

    async def fetch_all_sources(self) -> dict[str, int]:
        """抓取所有源资讯"""
        return await self._crawler.fetch_all_sources()

    async def fetch_remote_news(self, source: str, source_type: str = "flash") -> int:
        """抓取单一源资讯"""
        return await self._crawler.fetch_remote_news(source, source_type=source_type)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    async def list_sources(self) -> list[NewsSourceResponse]:
        """从消息来源表中查出启用配置"""
        result = await self.db.execute(
            select(NewsSource).where(NewsSource.enabled.is_(True)).order_by(NewsSource.sort_order, NewsSource.id)
        )
        return [NewsSourceResponse(code=source.code, name=source.name) for source in result.scalars().all()]

    async def list_flash_news(
        self,
        *,
        source: str = "cls",
        period: str = "today",
        important_only: bool = False,
        topic_name: str | None = None,
        cursor_time: datetime | None = None,
        cursor_id: int | None = None,
        limit: int = 20,
    ) -> NewsListResponse:
        sync_id = await self._source_high_watermark(source)
        # 1. 查出所有快讯数据
        stmt = self._news_select().where(NewsItem.content_type == "flash")
        # 2. 根据条件进行数据过滤
        stmt = self._apply_common_filters(
            stmt,
            source=source,
            period=period,
            important_only=important_only,
            topic_name=topic_name,
        )
        # 3. 根据时间进行游标过滤
        if cursor_time is not None and cursor_id is not None:
            if cursor_time.tzinfo is None:
                cursor_time = cursor_time.replace(tzinfo=SHANGHAI_TZ)
            stmt = stmt.where(
                or_(
                    NewsItem.published_at < cursor_time,
                    and_(NewsItem.published_at == cursor_time, NewsItem.id < cursor_id),
                )
            )

        # 4. 查询执行与"多查一条"技巧 用于判断是否还有更多数据
        stmt = stmt.order_by(desc(NewsItem.published_at), desc(NewsItem.id)).limit(limit + 1)
        result = await self.db.execute(stmt)
        items = list(result.scalars().unique().all())
        has_more = len(items) > limit
        page_items = items[:limit]
        next_cursor = None
        if has_more and page_items:
            last = page_items[-1]
            next_cursor = NewsCursorResponse(cursor_time=last.published_at, cursor_id=last.id)
        return NewsListResponse(
            items=[self._to_response(item) for item in page_items],
            next_cursor=next_cursor,
            sync_id=sync_id,
            has_more=has_more,
        )

    async def list_flash_updates(
        self,
        *,
        source: str = "cls",
        after_id: int,
        period: str = "today",
        important_only: bool = False,
        topic_name: str | None = None,
        limit: int = 100,
    ) -> NewsUpdatesResponse:
        """按入库 ID 拉取指定来源在同步水位之后的新快讯。"""
        source_watermark = await self._source_high_watermark(source)
        stmt = self._news_select().where(
            NewsItem.content_type == "flash",
            NewsItem.id > after_id,
        )
        stmt = self._apply_common_filters(
            stmt,
            source=source,
            period=period,
            important_only=important_only,
            topic_name=topic_name,
        )
        stmt = stmt.order_by(NewsItem.id).limit(limit + 1)
        result = await self.db.execute(stmt)
        items = list(result.scalars().unique().all())
        has_more = len(items) > limit
        page_items = items[:limit]

        last_item_id = page_items[-1].id if page_items else after_id
        sync_id = last_item_id if has_more else max(source_watermark, last_item_id)
        return NewsUpdatesResponse(
            items=[self._to_response(item) for item in page_items],
            sync_id=sync_id,
            has_more=has_more,
        )

    async def get_overview(
        self, *, source: str = "cls", period: str = "today", topic_limit: int = 10
    ) -> NewsOverviewResponse:
        # 检查合法来源
        self._require_query_source(source)
        # 根据period构造查询时间
        start_time = self._period_start(period)

        # 构造筛选条件
        filters = [NewsItem.content_type == "flash"]
        if start_time is not None:
            filters.append(NewsItem.published_at >= start_time)
        filters.append(NewsSource.code == source)

        # 计算快讯条数、重要快讯条数指标
        count_stmt = (
            select(
                func.count(NewsItem.id),
                func.count(NewsItem.id).filter(NewsItem.is_source_important.is_(True)),
            )
            .select_from(NewsItem)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .where(*filters)
        )
        total_count, important_count = (await self.db.execute(count_stmt)).one()

        # 查询主题数量
        topic_stmt = (
            select(NewsItemTopic.name, func.count(distinct(NewsItemTopic.news_item_id)).label("news_count"))
            .select_from(NewsItemTopic)
            .join(NewsItem, NewsItem.id == NewsItemTopic.news_item_id)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .where(*filters, NewsItemTopic.name.not_in(GENERIC_TOPIC_NAMES))
            .group_by(NewsItemTopic.name)
            .order_by(desc("news_count"), NewsItemTopic.name)
            .limit(topic_limit)
        )
        topic_rows = (await self.db.execute(topic_stmt)).all()

        return NewsOverviewResponse(
            total_count=int(total_count or 0),
            important_count=int(important_count or 0),
            top_topics=[NewsTopicCountResponse(name=name, news_count=int(count)) for name, count in topic_rows],
        )

    @staticmethod
    def _news_select():
        """工具函数 用于一次性查出信息对应的源，内容，主题，关联"""
        return select(NewsItem).options(
            selectinload(NewsItem.source),
            selectinload(NewsItem.topics),
            selectinload(NewsItem.entities),
            selectinload(NewsItem.relations),
        )

    async def _source_high_watermark(self, source: str) -> int:
        """返回指定来源当前最大的快讯入库 ID，不受页面筛选条件影响。"""
        self._require_query_source(source)
        stmt = (
            select(func.coalesce(func.max(NewsItem.id), 0))
            .select_from(NewsItem)
            .join(NewsSource, NewsSource.id == NewsItem.source_id)
            .where(
                NewsItem.content_type == "flash",
                NewsSource.code == source,
            )
        )
        return int((await self.db.execute(stmt)).scalar_one())

    @classmethod
    def _require_query_source(cls, source: str) -> None:
        """展示查询必须明确选择一个来源，禁止使用 all 聚合不同口径。"""
        if source not in NewsCrawler.SOURCES:
            raise ValueError(f"Unsupported news source: {source}")

    @staticmethod
    def _period_start(period: str) -> datetime | None:
        now = datetime.now(tz=SHANGHAI_TZ)
        if period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "week":
            return now - timedelta(days=7)
        if period == "all":
            return None
        raise ValueError(f"Unsupported news period: {period}")

    @staticmethod
    def _to_response(item: NewsItem) -> NewsItemResponse:
        return NewsItemResponse(
            id=item.id,
            source=NewsSourceResponse(code=item.source.code, name=item.source.name),
            content_type=item.content_type,
            title=item.title,
            content=item.content,
            is_source_important=bool(item.is_source_important),
            published_at=item.published_at,
            topics=[NewsTopicResponse(name=topic.name) for topic in item.topics],
            entities=[
                NewsEntityResponse(
                    type=entity.entity_type,
                    name=entity.name,
                    symbol=entity.symbol,
                )
                for entity in item.entities
            ],
            relations=[NewsRelationResponse(url=relation.url) for relation in item.relations],
        )

    def _apply_common_filters(
        self,
        stmt,
        *,
        source: str,
        period: str,
        important_only: bool,
        topic_name: str | None = None,
    ):
        """工具函数 根据传入的参数对stmt添加过滤数据逻辑"""
        self._require_query_source(source)
        # 1. 来源筛选
        stmt = stmt.join(NewsSource, NewsSource.id == NewsItem.source_id).where(NewsSource.code == source)
        start_time = self._period_start(period)
        # 2. 时间周期筛选
        if start_time is not None:
            stmt = stmt.where(NewsItem.published_at >= start_time)
        # 3. 是否重要筛选
        if important_only:
            stmt = stmt.where(NewsItem.is_source_important.is_(True))
        # 4. 主题名筛选
        if topic_name:
            topic_filters = [
                NewsItemTopic.news_item_id == NewsItem.id,
                NewsItemTopic.name == topic_name,
            ]
            stmt = stmt.where(exists(select(1).where(*topic_filters)))
        return stmt
