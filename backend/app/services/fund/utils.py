"""基金同步共用的数据清洗与批处理工具。"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


def normalize_fund_code(value: Any) -> str:
    """把 pandas object/数值代码标准化为六位基金代码。"""
    if value is None:
        raise ValueError("基金代码为空")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    code = str(value).strip().upper()
    if code.startswith(("SH", "SZ")):
        code = code[2:]
    if not code.isdigit() or len(code) > 6:
        raise ValueError(f"无效基金代码: {value!r}")
    return code.zfill(6)


def normalize_text(value: Any) -> str | None:
    """清理来源文本，并把常见空值表达统一为 None。"""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat", "--"}:
        return None
    return text


def normalize_decimal(value: Any) -> Decimal | None:
    """把来源数值或百分数字符串转换为 Decimal，不改变百分比量纲。"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip().replace(",", "").removesuffix("%")
    if not text or text.lower() in {"nan", "none", "nat", "--", "-"}:
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"无法转换数值: {value!r}") from exc


def normalize_date(value: Any) -> date | None:
    """转换 Python、pandas 日期值，并兼容 pandas.NaT/numpy.nan。"""
    if value is None:
        return None
    try:
        if value != value:  # pandas.NaT / numpy.nan，不强依赖 pandas。
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted = to_pydatetime()
        return converted.date() if isinstance(converted, datetime) else converted
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"无法转换日期: {value!r}") from exc


def dataframe_records(
        frame: Any,
        required_columns: set[str] | frozenset[str],
        source: str,
        minimum_rows: int = 1,
) -> list[dict[str, Any]]:
    """校验 DataFrame 列和最小行数，然后输出 records。"""
    columns = set(getattr(frame, "columns", []))
    missing = required_columns - columns
    if missing:
        raise ValueError(f"{source} 缺少字段: {sorted(missing)}")
    rows = frame.to_dict(orient="records")
    if len(rows) < minimum_rows:
        raise ValueError(f"{source} 返回行数异常: {len(rows)} < {minimum_rows}")
    return rows


def ensure_unique_fund_codes(rows: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    """确保一个来源快照中每个基金代码只出现一次。"""
    seen: set[str] = set()
    for row in rows:
        code = row["fund_code"]
        if code in seen:
            raise ValueError(f"{source} 返回重复基金代码: {code}")
        seen.add(code)
    return rows


def iter_batches(values: list[dict[str, Any]], size: int = 500) -> Iterable[list[dict[str, Any]]]:
    """把批量入库数据切成固定大小的批次。"""
    for index in range(0, len(values), size):
        yield values[index: index + size]
