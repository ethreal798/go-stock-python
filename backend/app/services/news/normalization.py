"""多来源解析共享的清洗与代码归一化函数。"""

import html
import re
from datetime import datetime, timezone
from typing import Any

HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"[ \t\f\v]+")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(WHITESPACE_RE.sub(" ", line).strip() for line in text.split("\n"))
    return "\n".join(line for line in text.split("\n") if line).strip()


def epoch_seconds(value: Any) -> datetime:
    timestamp = int(value)
    if timestamp <= 0:
        raise ValueError("发布时间必须是有效的 Unix 秒级时间戳")
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_stock_symbol(symbol: Any, market: str | None = None) -> str | None:
    """只接受并标准化 A 股、北交所和港股代码。"""
    raw = optional_str(symbol)
    if not raw:
        return None

    compact = raw.replace(" ", "")
    normalized_market = (market or "").upper()
    match = re.fullmatch(r"(?i)(sh|sz|bj)(\d{6})", compact)
    if match:
        return f"{match.group(2)}.{match.group(1).upper()}"

    match = re.fullmatch(r"(?i)(\d{6})\.(sh|sz|bj)", compact)
    if match:
        return f"{match.group(1)}.{match.group(2).upper()}"

    match = re.fullmatch(r"(?i)hk(\d{1,5})", compact)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    match = re.fullmatch(r"(?i)(\d{1,5})\.hk", compact)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    if normalized_market in {"HK", "HKG", "HKEX"} and re.fullmatch(r"\d{1,5}", compact):
        return f"{compact.zfill(5)}.HK"

    if re.fullmatch(r"\d{6}", compact):
        if normalized_market not in {"", "CN", "STOCK", "SB", "SH", "SZ", "BJ", "SSE", "SZSE", "BSE"}:
            return None
        if normalized_market in {"SH", "SSE"}:
            return f"{compact}.SH"
        if normalized_market in {"SZ", "SZSE"}:
            return f"{compact}.SZ"
        if normalized_market in {"BJ", "BSE"}:
            return f"{compact}.BJ"
        if compact.startswith(("4", "8")):
            return f"{compact}.BJ"
        if compact.startswith(("5", "6", "9")):
            return f"{compact}.SH"
        if compact.startswith(("0", "1", "2", "3")):
            return f"{compact}.SZ"

    return None
