"""来源解析器输出的统一 DTO。"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ParsedTopic:
    name: str


@dataclass(slots=True)
class ParsedEntity:
    entity_type: str
    name: str
    symbol: str


@dataclass(slots=True)
class ParsedRelation:
    url: str


@dataclass(slots=True)
class ParsedNewsItem:
    source_item_id: str
    published_at: datetime
    content: str
    content_type: str = "flash"
    title: str | None = None
    is_source_important: bool = False
    topics: list[ParsedTopic] = field(default_factory=list)
    entities: list[ParsedEntity] = field(default_factory=list)
    relations: list[ParsedRelation] = field(default_factory=list)
