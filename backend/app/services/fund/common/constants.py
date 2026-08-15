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
