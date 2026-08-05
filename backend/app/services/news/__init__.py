"""多源快讯解析组件。"""

from .cls_parser import parse_cls_item
from .dto import ParsedEntity, ParsedNewsItem, ParsedRelation, ParsedTopic
from .sina_parser import parse_sina_item
from .wscn_parser import parse_wscn_item

PARSERS = {
    "cls": parse_cls_item,
    "wscn": parse_wscn_item,
    "sina": parse_sina_item,
}

__all__ = [
    "PARSERS",
    "ParsedEntity",
    "ParsedNewsItem",
    "ParsedRelation",
    "ParsedTopic",
    "parse_cls_item",
    "parse_wscn_item",
    "parse_sina_item",
]
