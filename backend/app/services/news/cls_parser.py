"""财联社快讯解析器。"""

from typing import Any

from .dto import ParsedEntity, ParsedNewsItem, ParsedRelation, ParsedTopic
from .normalization import (
    clean_text,
    epoch_seconds,
    normalize_stock_symbol,
    optional_str,
)


def parse_cls_item(item: dict[str, Any]) -> ParsedNewsItem:
    source_item_id = optional_str(item.get("id"))
    if not source_item_id:
        raise ValueError("财联社快讯缺少 id")

    content = clean_text(item.get("content") or item.get("brief"))

    level = (optional_str(item.get("level")) or "").upper() or None

    # 外部原文只作为关联记录保存，不进入快讯主表。
    original_url = optional_str(item.get("assocArticleUrl"))

    topics: list[ParsedTopic] = []
    for subject in item.get("subjects") or []:
        if not isinstance(subject, dict):
            continue
        name = optional_str(subject.get("subject_name"))
        if not name:
            continue
        topics.append(ParsedTopic(name=name))

    entities: list[ParsedEntity] = []
    for stock in item.get("stock_list") or []:
        if not isinstance(stock, dict):
            continue
        name = optional_str(stock.get("name"))
        symbol = normalize_stock_symbol(stock.get("StockID"))
        if not symbol:
            continue
        entities.append(
            ParsedEntity(
                entity_type="stock",
                name=name or symbol,
                symbol=symbol,
            )
        )

    relations: list[ParsedRelation] = []
    if original_url:
        relations.append(ParsedRelation(url=original_url))

    return ParsedNewsItem(
        source_item_id=source_item_id,
        published_at=epoch_seconds(item.get("ctime")),
        content=content,
        title=optional_str(item.get("title")),
        is_source_important=level in {"A", "B"},
        topics=topics,
        entities=entities,
        relations=relations,
    )
