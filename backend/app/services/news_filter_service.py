"""新闻过滤与分类服务。

负责判断新闻是否与金融相关、计算相关性评分、分类打标。
"""

import re
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class NewsFilterService:
    """新闻过滤服务"""

    # 分类定义
    CATEGORY_MACRO = "macro"  # 宏观政策
    CATEGORY_INDUSTRY = "industry"  # 行业动态
    CATEGORY_COMPANY = "company"  # 公司新闻
    CATEGORY_REGULATORY = "regulatory"  # 监管动态
    CATEGORY_INTERNATIONAL = "international"  # 国际财经
    CATEGORY_OTHER = "other"  # 其他

    # 低价值关键词（直接过滤）
    FILTER_KEYWORDS = [
        "明星",
        "娱乐",
        "八卦",
        "出轨",
        "离婚",
        "结婚",
        "恋情",
        "体育",
        "足球",
        "篮球",
        "奥运会",
        "世界杯",
        "游戏",
        "电竞",
        "直播",
        "网红",
        "健康",
        "养生",
        "美容",
        "减肥",
        "旅游",
        "美食",
        "时尚",
        "穿搭",
        "星座",
        "运势",
        "解梦",
        "社会",
        "车祸",
        "火灾",
        "事故",
        "广告",
        "推广",
        "营销",
        "招商",
    ]

    # 宏观关键词
    MACRO_KEYWORDS = [
        "央行",
        "降准",
        "降息",
        "加息",
        "MLF",
        "LPR",
        "货币政策",
        "财政",
        "赤字",
        "国债",
        "地方债",
        "GDP",
        "CPI",
        "PPI",
        "PMI",
        "通胀",
        "通缩",
        "国务院",
        "发改委",
        "财政部",
        "统计局",
        "经济数据",
        "经济增长",
        "经济下行",
        "经济复苏",
        "汇率",
        "人民币",
        "美元",
        "外汇",
        "流动性",
        "放水",
        "缩表",
    ]

    # 行业关键词
    INDUSTRY_KEYWORDS = [
        "新能源",
        "光伏",
        "锂电",
        "电动车",
        "新能源汽车",
        "动力电池",
        "芯片",
        "半导体",
        "集成电路",
        "AI",
        "人工智能",
        "大模型",
        "消费",
        "白酒",
        "医药",
        "医疗",
        "生物",
        "房地产",
        "楼市",
        "房价",
        "住建部",
        "汽车",
        "销量",
        "产量",
        "出口",
        "贸易",
        "关税",
        "基建",
        "投资",
        "项目",
    ]

    # 公司关键词
    COMPANY_KEYWORDS = [
        "业绩",
        "财报",
        "年报",
        "季报",
        "预告",
        "净利润",
        "营收",
        "收购",
        "并购",
        "重组",
        "战略合作",
        "IPO",
        "上市",
        "退市",
        "定增",
        "配股",
        "大股东",
        "减持",
        "增持",
        "质押",
        "合同",
        "订单",
        "中标",
        "停产",
        "复产",
        "扩产",
    ]

    # 监管关键词
    REGULATORY_KEYWORDS = [
        "证监会",
        "银保监会",
        "监管",
        "新规",
        "政策",
        "立案",
        "调查",
        "处罚",
        "罚款",
        "问询函",
        "关注函",
        "警示函",
        "停牌",
        "复牌",
        "ST",
        "退市",
        "风险警示",
    ]

    # 国际关键词
    INTERNATIONAL_KEYWORDS = [
        "美联储",
        "加息",
        "降息",
        "非农",
        "CPI",
        "俄乌",
        "中东",
        "地缘",
        "冲突",
        "原油",
        "石油",
        "黄金",
        "大宗商品",
        "美股",
        "纳斯达克",
        "道琼斯",
        "标普",
        "欧股",
        "日经",
        "港股",
        "贸易战",
        "关税",
    ]

    # 加分关键词（高价值）
    BOOST_KEYWORDS = [
        "重磅",
        "突发",
        "刚刚",
        "最新",
        "超预期",
        "大超预期",
        "利好",
        "利空",
        "涨停",
        "跌停",
    ]

    @classmethod
    def analyze(cls, title: str, content: str) -> Tuple[bool, int, str]:
        """
        分析新闻，返回 (是否相关, 相关性评分, 分类)

        Args:
            title: 新闻标题
            content: 新闻内容

        Returns:
            (is_relevant, score, category)
        """
        text = f"{title} {content}".lower()

        # 1. 先检查是否为低价值内容
        if cls._is_low_value(text):
            return False, 0, cls.CATEGORY_OTHER

        # 2. 计算各分类的匹配度
        macro_score = cls._calc_category_score(text, cls.MACRO_KEYWORDS)
        industry_score = cls._calc_category_score(text, cls.INDUSTRY_KEYWORDS)
        company_score = cls._calc_category_score(text, cls.COMPANY_KEYWORDS)
        regulatory_score = cls._calc_category_score(text, cls.REGULATORY_KEYWORDS)
        international_score = cls._calc_category_score(text, cls.INTERNATIONAL_KEYWORDS)

        # 3. 找出最高分的分类
        scores = {
            cls.CATEGORY_MACRO: macro_score,
            cls.CATEGORY_INDUSTRY: industry_score,
            cls.CATEGORY_COMPANY: company_score,
            cls.CATEGORY_REGULATORY: regulatory_score,
            cls.CATEGORY_INTERNATIONAL: international_score,
        }

        max_category = max(scores.items(), key=lambda x: x[1])
        category = max_category[0] if max_category[1] > 0 else cls.CATEGORY_OTHER
        base_score = max_category[1]

        # 4. 加分项
        boost_score = cls._calc_boost_score(text)

        # 5. 计算最终评分（0-100）
        total_score = min(100, base_score + boost_score)

        # 6. 判断是否相关
        is_relevant = total_score >= 10  # 阈值可调整

        return is_relevant, total_score, category

    @classmethod
    def _is_low_value(cls, text: str) -> bool:
        """判断是否为低价值内容"""
        for keyword in cls.FILTER_KEYWORDS:
            if keyword in text:
                return True
        return False

    @classmethod
    def _calc_category_score(cls, text: str, keywords: list) -> int:
        """计算某一分类的得分"""
        score = 0
        for keyword in keywords:
            # 使用正则避免子串匹配问题（如"芯片"不会匹配"芯片测试"）
            if re.search(r"\b" + re.escape(keyword) + r"\b", text) or keyword in text:
                score += 10  # 每个关键词+10分
        return score

    @classmethod
    def _calc_boost_score(cls, text: str) -> int:
        """计算加分项"""
        score = 0
        for keyword in cls.BOOST_KEYWORDS:
            if keyword in text:
                score += 5
        return score
