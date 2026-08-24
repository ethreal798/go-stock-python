"""多源快讯解析与抓取组件。"""

from .cls_parser import parse_cls_item
from .crawler import NewsCrawler, PARSERS
from .dto import ParsedEntity, ParsedNewsItem, ParsedRelation, ParsedTopic
from .sina_parser import parse_sina_item
from .wscn_parser import parse_wscn_item

__all__ = [
    "NewsCrawler",
    "PARSERS",
    "ParsedEntity",
    "ParsedNewsItem",
    "ParsedRelation",
    "ParsedTopic",
    "parse_cls_item",
    "parse_wscn_item",
    "parse_sina_item",
]
