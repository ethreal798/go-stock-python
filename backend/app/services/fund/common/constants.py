"""基金服务共享常量。"""


class FundCacheKeys:
    """基金业务缓存键。"""

    @staticmethod
    def performance_trend(fund_code: str, period: str) -> str:
        return f"fund:performance-trend:v1:{fund_code}:{period}"


class FundRankingColumns:
    """东方财富三个基金排行接口的必需表头。"""

    OPEN = frozenset(
        {
            "基金代码",
            "基金简称",
            "日期",
            "单位净值",
            "累计净值",
            "日增长率",
            "近1周",
            "近1月",
            "近3月",
            "近6月",
            "近1年",
            "近2年",
            "近3年",
            "今年来",
            "成立来",
        }
    )

    EXCHANGE = frozenset(
        {
            "基金代码",
            "基金简称",
            "类型",
            "日期",
            "单位净值",
            "累计净值",
            "近1周",
            "近1月",
            "近3月",
            "近6月",
            "近1年",
            "近2年",
            "近3年",
            "今年来",
            "成立来",
            "成立日期",
        }
    )

    MONEY = frozenset(
        {
            "基金代码",
            "基金简称",
            "日期",
            "万份收益",
            "年化收益率7日",
            "年化收益率14日",
            "年化收益率28日",
            "近1月",
            "近3月",
            "近6月",
            "近1年",
            "近2年",
            "近3年",
            "近5年",
            "今年来",
            "成立来",
        }
    )


class FundHistoryColumns:
    """东方财富基金历史接口返回的必需表头。"""

    OPEN_UNIT_NAV = frozenset({"净值日期", "单位净值", "日增长率"})
    OPEN_ACCUMULATED_NAV = frozenset({"净值日期", "累计净值"})
    MONEY_YIELD = frozenset(
        {
            "净值日期",
            "每万份收益",
            "7日年化收益率",
            "申购状态",
            "赎回状态",
        }
    )
    EXCHANGE_NAV = frozenset(
        {
            "净值日期",
            "单位净值",
            "累计净值",
            "日增长率",
            "申购状态",
            "赎回状态",
        }
    )


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
