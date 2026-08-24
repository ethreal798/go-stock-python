"""基金服务共享常量。"""


class FundCacheKeys:
    """基金业务缓存键。"""

    @staticmethod
    def performance_trend(fund_code: str, period: str) -> str:
        return f"fund:performance-trend:v1:{fund_code}:{period}"


class FundMetadataColumns:
    """雪球基金档案和风险指标接口必需表头。"""

    PROFILE = frozenset({"item", "value"})
    RISK = frozenset(
        {
            "周期",
            "较同类风险收益比",
            "较同类抗风险波动",
            "年化波动率",
            "年化夏普比率",
            "最大回撤",
        }
    )


# ============================================================
# 基金排行字段映射配置
# ============================================================

# 周期字段（同时用于 sort 和 period 参数）
PERIOD_FIELDS: dict[str, tuple[str, str]] = {
    "1w": ("return_1w_pct", "近1周收益率"),
    "1m": ("return_1m_pct", "近1月收益率"),
    "3m": ("return_3m_pct", "近3月收益率"),
    "6m": ("return_6m_pct", "近6月收益率"),
    "1y": ("return_1y_pct", "近1年收益率"),
    "2y": ("return_2y_pct", "近2年收益率"),
    "3y": ("return_3y_pct", "近3年收益率"),
    "5y": ("return_5y_pct", "近5年收益率"),
    "ytd": ("return_ytd_pct", "今年以来收益率"),
    "since_inception": ("return_since_inception_pct", "成立以来收益率"),
}

# 周期字段 - 场内基金版（无 5y）
PERIOD_FIELDS_EXCHANGE: dict[str, tuple[str, str]] = {
    "1w": ("return_1w_pct", "近1周收益率"),
    "1m": ("return_1m_pct", "近1月收益率"),
    "3m": ("return_3m_pct", "近3月收益率"),
    "6m": ("return_6m_pct", "近6月收益率"),
    "1y": ("return_1y_pct", "近1年收益率"),
    "2y": ("return_2y_pct", "近2年收益率"),
    "3y": ("return_3y_pct", "近3年收益率"),
    "ytd": ("return_ytd_pct", "今年以来收益率"),
    "since_inception": ("return_since_inception_pct", "成立以来收益率"),
}

# 周期字段 - 货币基金版（无 1w）
PERIOD_FIELDS_MONEY: dict[str, tuple[str, str]] = {
    "1m": ("return_1m_pct", "近1月收益率"),
    "3m": ("return_3m_pct", "近3月收益率"),
    "6m": ("return_6m_pct", "近6月收益率"),
    "1y": ("return_1y_pct", "近1年收益率"),
    "2y": ("return_2y_pct", "近2年收益率"),
    "3y": ("return_3y_pct", "近3年收益率"),
    "5y": ("return_5y_pct", "近5年收益率"),
    "ytd": ("return_ytd_pct", "今年以来收益率"),
    "since_inception": ("return_since_inception_pct", "成立以来收益率"),
}

# 周期字段映射（period 参数）：category → period_key → (db_column, label)
PERIOD_FIELD_MAP: dict[str, dict[str, tuple[str, str]]] = {
    "open": dict(PERIOD_FIELDS),
    "exchange": dict(PERIOD_FIELDS_EXCHANGE),
    "money": dict(PERIOD_FIELDS_MONEY),
}

# 净值类字段（仅用于 sort，不可作为 period）
NAV_FIELDS: dict[str, tuple[str, str]] = {
    "nav": ("unit_nav", "最新净值"),
    "accumulated_nav": ("accumulated_nav", "累计净值"),
}

# 货币基金特有字段
MONEY_FIELDS: dict[str, tuple[str, str]] = {
    "income_per_10k": ("income_per_10k", "万份收益"),
    "annualized_7d": ("annualized_7d_pct", "7日年化收益率"),
    "annualized_14d": ("annualized_14d_pct", "14日年化收益率"),
    "annualized_28d": ("annualized_28d_pct", "28日年化收益率"),
}

# 各分类支持的 sort 字段映射：category → sort_key → (db_column, label)
SORT_FIELD_MAP: dict[str, dict[str, tuple[str, str]]] = {
    "open": {**PERIOD_FIELDS, **NAV_FIELDS},
    "exchange": {**PERIOD_FIELDS_EXCHANGE, **NAV_FIELDS},
    "money": {**PERIOD_FIELDS_MONEY, **MONEY_FIELDS},
}
