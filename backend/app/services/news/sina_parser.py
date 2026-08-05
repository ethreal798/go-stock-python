"""新浪财经 7×24 快讯解析器。"""

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .dto import ParsedEntity, ParsedNewsItem, ParsedTopic
from .normalization import clean_text, normalize_stock_symbol, optional_str

TITLE_RE = re.compile(r"^【([^】]+)】\s*(.*)$", re.S)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def _parse_ext(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def parse_sina_item(item: dict[str, Any]) -> ParsedNewsItem:
    #
    source_item_id = optional_str(item.get("id"))
    if not source_item_id:
        raise ValueError("新浪财经快讯缺少 id")

    raw_content = clean_text(item.get("rich_text"))
    if not raw_content:
        raise ValueError(f"新浪财经快讯 {source_item_id} 缺少正文")

    title = None
    content = raw_content
    title_match = TITLE_RE.match(raw_content)
    if title_match:
        title = title_match.group(1).strip() or None
        content = title_match.group(2).strip() or raw_content

    create_time = optional_str(item.get("create_time"))
    if not create_time:
        raise ValueError(f"新浪财经快讯 {source_item_id} 缺少 create_time")
    published_at = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SHANGHAI_TZ)

    ext = _parse_ext(item.get("ext"))

    topics: list[ParsedTopic] = []
    for tag in item.get("tag") or []:
        if not isinstance(tag, dict):
            continue
        name = optional_str(tag.get("name"))
        if name:
            topics.append(ParsedTopic(name=name))

    entities: list[ParsedEntity] = []
    for stock in ext.get("stocks") or []:
        if not isinstance(stock, dict):
            continue
        source_type = (optional_str(stock.get("market")) or "").lower()
        raw_symbol = optional_str(stock.get("symbol"))
        name = optional_str(stock.get("key"))
        if not raw_symbol:
            continue
        if source_type == "fund":
            entity_type = "fund"
            symbol = raw_symbol
        else:
            entity_type = "stock"
            symbol = normalize_stock_symbol(raw_symbol, source_type)
            if not symbol:
                continue
        entities.append(
            ParsedEntity(
                entity_type=entity_type,
                name=name or symbol,
                symbol=symbol,
            )
        )

    is_source_important = any(topic.name == "焦点" for topic in topics)

    return ParsedNewsItem(
        source_item_id=source_item_id,
        published_at=published_at,
        content=content,
        title=title,
        is_source_important=is_source_important,
        topics=topics,
        entities=entities,
    )
