"""多源财经快讯采集、入库与查询服务。"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import and_, desc, distinct, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.sse import sse_manager
from app.models.news import (
    NewsItem,
    NewsItemEntity,
    NewsItemRelation,
    NewsItemTopic,
    NewsRawItem,
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
from app.services.news import PARSERS, ParsedEntity, ParsedNewsItem, ParsedRelation, ParsedTopic

logger = logging.getLogger(__name__)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
GENERIC_TOPIC_NAMES = {"其他", "全球", "7x24快讯", "7×24快讯", "选股宝"}


class NewsService:
    """三个快讯来源的后端统一入口。"""

    SOURCES: dict[str, dict[str, str]] = {
        "cls": {
            "name": "财联社",
            "url": "https://www.cls.cn/api/cache?app=CailianpressWeb&name=telegraph&os=web&sv=8.7.9",
        },
        "wscn": {
            "name": "华尔街见闻",
            "url": "https://api-one-wscn.awtmt.com/apiv1/content/lives",
        },
        "sina": {
            "name": "新浪财经",
            "url": "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=20&zhibo_id=152",
        },
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 采集与入库
    # ------------------------------------------------------------------

    async def fetch_all_sources(self) -> dict[str, int]:
        results: dict[str, int] = {}
        for source_code in self.SOURCES:
            results[source_code] = await self.fetch_remote_news(source_code)
        return results

    async def fetch_remote_news(self, source: str, source_type: str = "flash") -> int:
        """抓取一个来源。V1 仅支持 flash，参数保留用于调度器兼容。"""
        if source_type not in {"flash"}:
            logger.debug("Skip unsupported news content type: source=%s type=%s", source, source_type)
            return 0
        if source not in self.SOURCES:
            logger.warning("Unknown news source: %s", source)
            return 0

        try:
            items = await self._fetch_source_items(source)
            return await self._save_news_batch(items, source)
        except Exception:
            logger.exception("News source crawl failed: source=%s", source)
            await self.db.rollback()
            return 0

    async def _fetch_source_items(self, source: str) -> list[dict[str, Any]]:
        config = self.SOURCES[source]
        url = config["url"].strip()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        params: dict[str, Any] | None = None
        if source == "cls":
            headers["Referer"] = "https://www.cls.cn/"
        elif source == "wscn":
            params = {"channel": "global-channel", "client": "pc", "limit": 20}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        if source == "cls":
            items = payload.get("data", {}).get("roll_data", [])
        elif source == "wscn":
            if payload.get("code") != 20000:
                raise ValueError(f"华尔街见闻接口返回失败: {payload.get('message')}")
            items = payload.get("data", {}).get("items", [])
        else:
            result = payload.get("result", {})
            status = result.get("status", {})
            if status.get("code") != 0:
                raise ValueError(f"新浪财经接口返回失败: {status.get('msg')}")
            items = result.get("data", {}).get("feed", {}).get("list", [])

        if not isinstance(items, list):
            raise ValueError(f"来源 {source} 的快讯列表不是数组")
        return [item for item in items if isinstance(item, dict)]

    async def _save_news_batch(self, items: list[dict[str, Any]], source_code: str) -> int:
        # 1. 如果当前源在数据库不存在则新建记录
        source = await self._get_or_create_source(source_code)
        # 2. 获取对应源的解析方法
        parser = PARSERS[source_code]
        inserted_count = 0

        for payload in items:
            try:
                parsed = parser(payload)
                #
                inserted = await self._insert_parsed_item(source, payload, parsed)
                inserted_count += int(inserted)
            except Exception:
                logger.exception(
                    "News item parse/insert failed: source=%s source_item_id=%s",
                    source_code,
                    payload.get("id"),
                )

        if inserted_count:
            await self.db.commit()
            await sse_manager.broadcast(
                json.dumps(
                    {"event": "news_flash", "source": source_code, "count": inserted_count},
                    ensure_ascii=False,
                )
            )
            logger.info("News batch inserted: source=%s count=%s", source_code, inserted_count)
        else:
            # 结束查询开启的只读事务，避免调度器后续阶段持有无用事务。
            await self.db.rollback()
        return inserted_count

    async def _get_or_create_source(self, source_code: str) -> NewsSource:
        """如果当前配置抓取源在来源表中不存在则创建记录"""
        result = await self.db.execute(select(NewsSource).where(NewsSource.code == source_code))
        source = result.scalar_one_or_none()
        if source:
            return source

        source = NewsSource(code=source_code, name=self.SOURCES[source_code]["name"], enabled=True)
        self.db.add(source)
        await self.db.flush()
        return source

    async def _insert_parsed_item(self, source: NewsSource, payload: dict[str, Any], parsed: ParsedNewsItem) -> bool:
        """数据入库"""
        async with self.db.begin_nested():
            raw_insert = (
                pg_insert(NewsRawItem)
                .values(
                    source_id=source.id,
                    source_item_id=parsed.source_item_id,
                    payload=payload,
                    published_at=parsed.published_at,
                )
                .on_conflict_do_nothing(constraint="uq_news_raw_source_item")
                .returning(NewsRawItem.id)
            )
            raw_result = await self.db.execute(raw_insert)
            raw_item_id = raw_result.scalar_one_or_none()
            if raw_item_id is None:
                return False

            news_item = NewsItem(
                raw_item_id=raw_item_id,
                source_id=source.id,
                content_type=parsed.content_type,
                title=parsed.title,
                content=parsed.content,
                is_source_important=parsed.is_source_important,
                published_at=parsed.published_at,
            )
            self.db.add(news_item)
            await self.db.flush()

            self.db.add_all(self._build_topic_models(news_item.id, parsed.topics))
            self.db.add_all(self._build_entity_models(news_item.id, parsed.entities))
            self.db.add_all(self._build_relation_models(news_item.id, parsed.relations))
            await self.db.flush()
            return True

    @staticmethod
    def _build_topic_models(news_item_id: int, topics: list[ParsedTopic]) -> list[NewsItemTopic]:
        models: list[NewsItemTopic] = []
        seen: set[str] = set()
        for topic in topics:
            if not topic.name or topic.name in seen:
                continue
            seen.add(topic.name)
            models.append(
                NewsItemTopic(
                    news_item_id=news_item_id,
                    name=topic.name,
                )
            )
        return models

    @staticmethod
    def _build_entity_models(news_item_id: int, entities: list[ParsedEntity]) -> list[NewsItemEntity]:
        models: list[NewsItemEntity] = []
        seen: set[tuple[str, str]] = set()
        for entity in entities:
            key = (entity.entity_type, entity.symbol)
            if not entity.symbol or key in seen:
                continue
            seen.add(key)
            models.append(
                NewsItemEntity(
                    news_item_id=news_item_id,
                    entity_type=entity.entity_type,
                    symbol=entity.symbol,
                    name=entity.name,
                )
            )
        return models

    @staticmethod
    def _build_relation_models(news_item_id: int, relations: list[ParsedRelation]) -> list[NewsItemRelation]:
        models: list[NewsItemRelation] = []
        seen: set[str] = set()
        for relation in relations:
            if not relation.url or relation.url in seen:
                continue
            seen.add(relation.url)
            models.append(NewsItemRelation(news_item_id=news_item_id, url=relation.url))
        return models

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    async def list_sources(self) -> list[NewsSourceResponse]:
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

        # 4. 查询执行与“多查一条”技巧 用于判断是否还有更多数据
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
        if source not in cls.SOURCES:
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
        stmt = stmt.join(NewsSource, NewsSource.id == NewsItem.source_id).where(NewsSource.code == source)
        start_time = self._period_start(period)
        if start_time is not None:
            stmt = stmt.where(NewsItem.published_at >= start_time)
        if important_only:
            stmt = stmt.where(NewsItem.is_source_important.is_(True))
        if topic_name:
            topic_filters = [
                NewsItemTopic.news_item_id == NewsItem.id,
                NewsItemTopic.name == topic_name,
            ]
            stmt = stmt.where(exists(select(1).where(*topic_filters)))
        return stmt
