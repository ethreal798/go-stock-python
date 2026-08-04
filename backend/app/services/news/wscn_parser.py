"""华尔街见闻快讯解析器。"""

from typing import Any

from .dto import ParsedEntity, ParsedNewsItem, ParsedTopic
from .normalization import clean_text, epoch_seconds, normalize_stock_symbol, optional_str

CHANNEL_NAMES = {
    "global-channel": "全球",
    "a-stock-channel": "A股",
    "hk-stock-channel": "港股",
    "us-stock-channel": "美股",
    "forex-channel": "外汇",
    "commodity-channel": "大宗商品",
    "oil-channel": "原油",
    "gold-channel": "黄金",
    "goldc-channel": "黄金",
    "bond-channel": "债券",
    "cryptocurrency-channel": "加密货币",
    "xgb-channel": "选股宝",
}


def _entity_from_symbol(value: Any, entity_type: str) -> ParsedEntity | None:
    if isinstance(value, dict):
        raw_symbol = optional_str(value.get("symbol") or value.get("code"))
        name = optional_str(value.get("name") or value.get("title"))
        market = optional_str(value.get("market"))
    else:
        raw_symbol = optional_str(value)
        name = raw_symbol
        market = None
    if not raw_symbol and not name:
        return None
    symbol = optional_str(raw_symbol) if entity_type == "fund" else normalize_stock_symbol(raw_symbol, market)
    if not symbol:
        return None
    return ParsedEntity(
        entity_type=entity_type,
        name=name or symbol,
        symbol=symbol,
    )


def parse_wscn_item(item: dict[str, Any]) -> ParsedNewsItem:
    source_item_id = optional_str(item.get("id"))
    if not source_item_id:
        raise ValueError("华尔街见闻快讯缺少 id")

    content = clean_text(item.get("content_text") or item.get("content"))
    if not content:
        raise ValueError(f"华尔街见闻快讯 {source_item_id} 缺少正文")
    content_more = clean_text(item.get("content_more"))
    if content_more:
        content = f"{content}\n\n{content_more}"

    topics: list[ParsedTopic] = []
    for channel in item.get("channels") or []:
        code = optional_str(channel)
        if code:
            topics.append(ParsedTopic(name=CHANNEL_NAMES.get(code, code)))

    entities = [
        entity
        for entity in (
            *(_entity_from_symbol(symbol, "stock") for symbol in item.get("symbols") or []),
            *(_entity_from_symbol(code, "fund") for code in item.get("fund_codes") or []),
        )
        if entity is not None
    ]

    score = int(item.get("score") or 0)

    return ParsedNewsItem(
        source_item_id=source_item_id,
        published_at=epoch_seconds(item.get("display_time")),
        content=content,
        title=optional_str(clean_text(item.get("title"))),
        is_source_important=score >= 2,
        topics=topics,
        entities=entities,
    )
