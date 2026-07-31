"""新闻资讯服务。

负责从财联社、华尔街见闻、新浪财经、东方财富等源获取快讯和要闻。
"""

import re
import logging
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Telegraph
from app.schemas.news import TelegraphResponse
from app.core.sse import sse_manager
from app.services.news_filter_service import NewsFilterService

logger = logging.getLogger(__name__)


class NewsService:
    """新闻资讯服务"""

    # 数据源配置
    SOURCES: dict[str: dict] = {
        "cls": {
            "name": "财联社",
            "url": "https://www.cls.cn/nodeapi/telegraphList"
        },
        "wscn": {
            "name": "华尔街见闻",
            "url": "https://api-one-wscn.awtmt.com/apiv1/content/lives"
        },
        "sina": {
            "name": "新浪财经快讯",
            "url": "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=20&zhibo_id=152",
        },
        "sina_market": {
            "name": "新浪市场要闻",
            "source_type": "news",
            "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=20&page=1",
        },
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_telegraphs(
            self, 
            source: str = "all", 
            source_type: str = "fast", 
            limit: int = 20, 
            page: int = 1, 
            relevant_only: bool = True
    ) -> List[TelegraphResponse]:
        """获取电报快讯或市场要闻（纯查库）。"""
        stmt = select(Telegraph).where(Telegraph.source_type == source_type)

        if source != "all" and source in self.SOURCES:
            source_name = self.SOURCES[source]["name"]
            stmt = stmt.where(Telegraph.source.contains(source_name))

        if relevant_only:
            stmt = stmt.where(Telegraph.is_relevant == bool(1))

        stmt = stmt.order_by(desc(Telegraph.data_time)).limit(limit).offset((page - 1) * limit)

        result = await self.db.execute(stmt)
        telegraphs = result.scalars().all()

        return [
            TelegraphResponse(
                id=t.id,
                time=t.time,
                data_time=t.data_time,
                title=t.title or "",
                content=t.content,
                is_red=t.is_red,
                url=t.url or "",
                source=t.source,
                sentiment_result=t.sentiment_result or "Neutral",
                subjects=[],
                stocks=[],
                is_relevant=t.is_relevant,
                relevance_score=t.relevance_score or 0,
                category=t.category,
            )
            for t in telegraphs
        ]

    async def fetch_all_sources(self) -> Dict[str, int]:
        """后台定时任务调用：抓取所有源。"""
        results = {}
        for source in self.SOURCES.keys():
            source_type = self.SOURCES.get(source).get("source_type", "fast")
            count = await self.fetch_remote_news(source, source_type)
            results[source] = count

        return results

    async def fetch_remote_news(self, source: str, source_type: str) -> int:
        """从远程接口抓取最新新闻并入库。"""
        try:
            if source == "cls":
                return await self._fetch_cls_news(source_type)
            elif source == "wscn":
                return await self._fetch_wscn_news(source_type)
            elif source == "sina":
                return await self._fetch_sina_news(source_type)
            elif source == "sina_market":
                return await self._fetch_sina_market_news(source_type)
            return 0
        except Exception as e:
            logger.error(f"Error fetching remote news from {source}: {e}")
            return 0

    async def _fetch_cls_news(self, source_type: str) -> int:
        """抓取财联社电报。"""
        url = self.SOURCES["cls"]["url"]
        headers = {
            "Referer": "https://www.cls.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return 0

                data = response.json()
                items = data.get("data", {}).get("roll_data", [])
                return await self._save_news_batch(items, "cls", source_type)

            except Exception as e:
                logger.error(f"CLS API Error: {e}")
                return 0

    async def _fetch_wscn_news(self, source_type: str) -> int:
        """抓取华尔街见闻快讯。"""
        params = {"channel": "global-channel", "client": "pc", "limit": 20}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.SOURCES["wscn"]["url"], params=params, headers=headers)
                data = response.json()
                items = data.get("data", {}).get("items", [])
                return await self._save_news_batch(items, "wscn", source_type)
            except Exception as e:
                logger.error(f"WSCN API Error: {e}")
                return 0

    async def _fetch_sina_news(self, source_type: str) -> int:
        """抓取新浪财经直播快讯。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.SOURCES["sina"]["url"])
                data = response.json()
                items = data.get("result", {}).get("data", {}).get("feed", {}).get("list", [])
                return await self._save_news_batch(items, "sina", source_type)
            except Exception as e:
                logger.error(f"Sina API Error: {e}")
                return 0

    async def _fetch_sina_market_news(self, source_type: str = "news") -> int:
        """抓取新浪市场要闻。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.SOURCES["sina_market"]["url"])
                data = response.json()
                items = data.get("result", {}).get("data", [])
                return await self._save_news_batch(items, "sina_market", source_type)
            except Exception as e:
                logger.error(f"Sina Market API Error: {e}")
                return 0

    async def _save_news_batch(self, items: List[Dict[str, Any]], source_key: str, source_type: str) -> int:
        """通用的批量入库逻辑。"""
        count = 0
        source_name = self.SOURCES[source_key]["name"]

        for item in items:
            parsed = self._parse_item(item, source_key)
            if not parsed or not parsed["content"]:
                continue

            stmt = select(Telegraph).where(Telegraph.content == parsed["content"])
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                continue

            # 使用过滤服务分析新闻
            is_relevant, relevance_score, category = NewsFilterService.analyze(parsed["title"] or "", parsed["content"])

            new_news = Telegraph(
                title=parsed["title"],
                content=parsed["content"],
                time=parsed["data_time"].strftime("%H:%M:%S"),
                data_time=parsed["data_time"],
                url=parsed["url"],
                source=source_name,
                is_red=parsed["is_red"],
                source_type=source_type,
                sentiment_result="Neutral",
                is_relevant=is_relevant,
                relevance_score=relevance_score,
                category=category,
            )
            self.db.add(new_news)
            count += 1

        if count > 0:
            await self.db.commit()
            logger.info(f"Successfully fetched {count} {source_type} news from {source_name}")
            # 发送 SSE 信号通知前端刷新
            await sse_manager.broadcast("refresh")

        return count

    def _parse_item(self, item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """解析不同源的数据字段。"""
        try:
            if source == "eastmoney":
                content = item.get("digest", "")
                return {
                    "title": item.get("title", ""),
                    "content": self._clean_html(content),
                    "data_time": datetime.strptime(item.get("showtime", ""), "%Y-%m-%d %H:%M:%S"),
                    "url": item.get("url", ""),
                    "is_red": False,
                }
            elif source == "cls":
                return {
                    "title": item.get("title", ""),
                    "content": self._clean_html(item.get("content", "")),
                    "data_time": datetime.fromtimestamp(item.get("ctime", 0)),
                    "url": item.get("shareurl", ""),
                    "is_red": item.get("level", "") != "C",
                }
            elif source == "wscn":
                content = item.get("content_text", "") or item.get("content", "")
                return {
                    "title": item.get("title", ""),
                    "content": self._clean_html(content),
                    "data_time": datetime.fromtimestamp(item.get("display_time", 0)),
                    "url": item.get("uri", ""),
                    "is_red": item.get("score", 0) > 1,
                }
            elif source == "sina":
                content = item.get("rich_text", "")
                create_time = item.get("create_time", "")
                try:
                    dt = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt = datetime.now()
                return {
                    "title": "",
                    "content": self._clean_html(content),
                    "data_time": dt,
                    "url": "",
                    "is_red": "焦点" in item.get("tag", []),
                }
            elif source == "sina_market":
                content = item.get("intro", "") or item.get("title", "")
                dt = datetime.fromtimestamp(int(item.get("ctime", 0)))
                return {
                    "title": item.get("title", ""),
                    "content": self._clean_html(content),
                    "data_time": dt,
                    "url": item.get("url", ""),
                    "is_red": False,
                }
        except Exception as e:
            logger.warning(f"Parse error for {source}: {e}")
        return None

    def _clean_html(self, text: str) -> str:
        """清理 HTML 标签和多余空格。"""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&nbsp;", " ").strip()
        return text
