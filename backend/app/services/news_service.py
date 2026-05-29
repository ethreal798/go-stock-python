"""新闻资讯服务。

负责从财联社、华尔街见闻、新浪财经等源获取快讯。
"""

import re
import logging
import httpx
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Telegraph, Tags, TelegraphTags
from app.schemas.news import TelegraphResponse

logger = logging.getLogger(__name__)


class NewsService:
    """新闻资讯服务"""

    CLS_URL = "https://www.cls.cn/nodeapi/telegraphList"
    WSCN_URL = "https://api-one-wscn.awtmt.com/apiv1/content/lives"
    SINA_URL = "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=20&zhibo_id=152"

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
        source_name = "财联社电报" if source == "cls" else ("华尔街见闻" if source == "wscn" else "新浪财经")
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

    async def fetch_remote_news(self, source: str = "cls") -> int:
        """从远程接口抓取最新新闻并入库。"""
        try:
            if source == "cls":
                count = await self._fetch_cls_news()
                if count == 0:
                    logger.info("CLS API returned no data, falling back to HTML scraping...")
                    count = await self._fetch_cls_html()
                return count
            elif source == "wscn":
                return await self._fetch_wscn_news()
            elif source == "sina":
                return await self._fetch_sina_news()
            return 0
        except Exception as e:
            logger.error(f"Error fetching remote news from {source}: {e}")

    async def _fetch_cls_news(self) -> int:
        """抓取财联社电报 (API方式)"""
        headers = {
            "Referer": "https://www.cls.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.CLS_URL, headers=headers)
                if response.status_code != 200:
                    logger.warning(f"CLS API returned status {response.status_code}")
                    return 0


                data = response.json()
                roll_data = data.get("data", {}).get("roll_data", [])
                return await self._process_cls_items(roll_data)

            except Exception as e:
                logger.exception(f"CLS API Error: {e}")
                return 0

    async def _fetch_cls_html(self) -> int:
        """抓取财联社电报 (HTML 网页爬取降级)。"""
        url = "https://www.cls.cn/telegraph"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return 0

                html = response.text
                # 匹配电报内容
                items = re.findall(r'<span class="telegraph-content-box">.*?<span>(.*?)</span>.*?</span>', html, re.S)

                count = 0
                for content in items:
                    content = re.sub(r'<[^>]+>', '', content).strip()
                    if not content: continue

                    stmt = select(Telegraph).where(Telegraph.content == content)
                    existing = await self.db.execute(stmt)
                    if existing.scalar_one_or_none():
                        continue

                    dt = datetime.now()
                    new_news = Telegraph(
                        content=content,
                        time=dt.strftime("%H:%M:%S"),
                        data_time=dt,
                        source="财联社电报(HTML)",
                        sentiment_result="Neutral"
                    )
                    self.db.add(new_news)
                    count += 1

                await self.db.commit()
                return count
            except Exception as e:
                logger.error(f"CLS HTML Scraping Error: {e}")
                return 0

    async def _process_cls_items(self, items: list) -> int:
        """统一处理财联社数据入库。"""
        count = 0
        for item in items:
            content = item.get("content", "")
            title = item.get("title", "")
            if not content: continue

            stmt = select(Telegraph).where(
                (Telegraph.content == content) | (Telegraph.title == title) if title else (Telegraph.content == content)
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                continue

            ctime = item.get("ctime", 0)
            dt = datetime.fromtimestamp(ctime)

            new_news = Telegraph(
                title=title,
                content=content,
                time=dt.strftime("%H:%M:%S"),
                data_time=dt,
                url=item.get("shareurl", ""),
                source="财联社电报",
                is_red=item.get("level", "") != "C",
                sentiment_result="Neutral"
            )
            self.db.add(new_news)
            count += 1
        await self.db.commit()
        return count

    async def _fetch_wscn_news(self) -> int:
        """抓取华尔街见闻快讯。"""
        params = {
            "channel": "global-channel",
            "client": "pc",
            "limit": 20,
            "first_page": "true",
            "accept": "live,vip-live"
        }
        headers = {
            "Referer": "https://wallstreetcn.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.WSCN_URL, params=params, headers=headers)
                data = response.json()
                if data.get("code") != 20000:
                    return 0

                items = data.get("data", {}).get("items", [])
                count = 0
                for item in items:
                    content = item.get("content_text", "") or item.get("content", "")
                    # 清理 HTML 标签 (简单处理)
                    import re
                    content = re.sub(r'<[^>]+>', '', content).strip()

                    title = item.get("title", "")

                    stmt = select(Telegraph).where(
                        (Telegraph.content == content) | (Telegraph.title == title) if title else (
                                    Telegraph.content == content)
                    )
                    existing = await self.db.execute(stmt)
                    if existing.scalar_one_or_none():
                        continue

                    dt = datetime.fromtimestamp(item.get("display_time", 0))

                    new_news = Telegraph(
                        title=title,
                        content=content,
                        time=dt.strftime("%H:%M:%S"),
                        data_time=dt,
                        url=item.get("uri", ""),
                        source="华尔街见闻",
                        is_red=item.get("score", 0) > 1,
                        sentiment_result="Neutral"
                    )
                    self.db.add(new_news)
                    count += 1

                await self.db.commit()
                return count
            except Exception as e:
                logger.exception("Error fetching WSCN news: %s", e)
                return 0

    async def _fetch_sina_news(self) -> int:
        """抓取新浪财经直播。"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.SINA_URL)
                data = response.json()
                if data.get("result", {}).get("status", {}).get("code") != 0:
                    return 0

                feed_list = data.get("result", {}).get("data", {}).get("feed", {}).get("list", [])
                count = 0
                for item in feed_list:
                    content = item.get("rich_text", "")
                    if not content: continue

                    content = re.sub(r'<[^>]+>', '', content).strip()

                    stmt = select(Telegraph).where(Telegraph.content == content)
                    existing = await self.db.execute(stmt)
                    if existing.scalar_one_or_none():
                        continue

                    create_time = item.get("create_time", "")
                    try:
                        dt = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    except:
                        dt = datetime.now()

                    new_news = Telegraph(
                        content=content,
                        time=dt.strftime("%H:%M:%S"),
                        data_time=dt,
                        source="新浪财经",
                        is_red="焦点" in item.get("tag", []),
                        sentiment_result="Neutral"
                    )
                    self.db.add(new_news)
                    count += 1
                await self.db.commit()
                return count
            except Exception as e:
                logger.error(f"Sina News Error: {e}")
                return 0