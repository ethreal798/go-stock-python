"""基金业务逻辑服务。"""

import re
import json
import logging
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FollowedFund

logger = logging.getLogger(__name__)


class FundService:
    """基金服务类"""

    # 天天基金全量列表接口 (包含约 1.5w 只基金)
    FUND_LIST_URL = "http://fund.eastmoney.com/js/fundcode_search.js"
    # 基金估值/基础信息接口
    FUND_GZ_URL = "https://fundgz.1234567.com.cn/js/{code}.js"
    # 基金净值历史接口 (用于获取最新准确净值)
    FUND_LSJZ_URL = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code={code}&page=1&per=1"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_fund_detail(self, code: str) -> Optional[Fund]:
        """获取基金详情（包含实时刷新逻辑）。"""
        stmt = select(Fund).where(Fund.code == code)
        result = await self.db.execute(stmt)
        fund = result.scalar_one_or_none()

        if not fund:
            return None

        # 如果数据超过 1 小时未更新，则触发刷新  1小时会不会太久了
        now = datetime.now()
        if not fund.last_update or (now - fund.last_update).total_seconds() > 3600:
            if await self.refresh_fund_detail(fund):
                result = await self.db.execute(stmt)
                fund = result.scalar_one_or_none()

        return fund

    async def refresh_fund_detail(self, fund: Fund) -> bool:
        """刷新基金详情数据。"""
        try:
            # 1. 获取最新净值和日增长率 (从 LSJZ 接口获取最准确的昨日净值)
            lsjz_url = self.FUND_LSJZ_URL.format(code=fund.code)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(lsjz_url)
                if resp.status_code == 200:
                    # 解析 var apidata={ content:"...", ...}
                    match = re.search(r'content:"(.*?)",', resp.text)
                    if match:
                        content = match.group(1)
                        # 提取第一行数据: <td>2026-06-08</td><td class='tor bold'>1.2400</td>
                        # <td class='tor bold'>3.8130</td><td class='tor bold grn'>-2.82%</td>
                        row_match = re.search(
                            r"<td>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td>", content
                        )
                        if row_match:
                            date_str, nav, acc_nav, growth = row_match.groups()
                            fund.nav = float(nav)
                            fund.acc_nav = float(acc_nav)
                            # 清理增长率中的百分号和 HTML 标签
                            growth_clean = re.sub(r"<[^>]+>", "", growth).replace("%", "")
                            fund.day_growth = float(growth_clean)
                            fund.last_update = datetime.now()

            # 2. 获取阶段涨幅 (从 H5 详情页解析)
            detail_url = f"https://fundf10.eastmoney.com/tsdata_{fund.code}.html"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(detail_url)
                if resp.status_code == 200:
                    html = resp.text
                    # 解析阶段涨幅表格
                    # 格式通常是: <td class='...'>近1周</td><td class='...'>-0.24%</td>
                    periods = {
                        "week_growth": "近1周",
                        "month_growth": "近1月",
                        "three_month_growth": "近3月",
                        "six_month_growth": "近6月",
                        "year_growth": "近1年",
                        "current_year_growth": "今年以来",
                    }
                    for attr, label in periods.items():
                        # 更加宽松的正则匹配
                        match = re.search(rf"<td>{label}</td><td.*?>(.*?)%</td>", html)
                        if not match:
                            # 尝试带 class 的匹配
                            match = re.search(rf"<td.*?>{label}</td><td.*?>(.*?)%</td>", html)

                        if match:
                            try:
                                val_str = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                                val = float(val_str)
                                setattr(fund, attr, val)
                            except Exception:
                                pass

                    # 尝试解析基金经理 (更加宽松的正则)
                    manager_match = re.search(r"基金经理.*?<a.*?>([\u4e00-\u9fa5]+)</a>", html)
                    if manager_match:
                        fund.manager = manager_match.group(1)

            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error refreshing fund {fund.code}: {e}")
            return False

    async def get_funds(self, keyword: Optional[str] = None, limit: int = 20, page: int = 1, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """查询基金列表（支持搜索），带关注状态。"""
        stmt = select(Fund)

        if keyword:
            # 支持代码、名称模糊搜索
            stmt = stmt.where(or_(Fund.code.contains(keyword), Fund.name.contains(keyword)))

        # 默认按代码排序
        stmt = stmt.order_by(Fund.code).limit(limit).offset((page - 1) * limit)

        result = await self.db.execute(stmt)
        funds = list(result.scalars().all())
        
        # 组装返回结果，包含关注状态
        followed_codes = set()
        if user_id:
            followed_stmt = select(FollowedFund).where(FollowedFund.user_id == user_id)
            followed_result = await self.db.execute(followed_stmt)
            followed_codes = {f.fund_code for f in followed_result.scalars().all()}
        
        return [
            {
                "id": fund.id,
                "code": fund.code,
                "name": fund.name,
                "type": fund.type,
                "nav": fund.nav,
                "acc_nav": fund.acc_nav,
                "day_growth": fund.day_growth,
                "week_growth": fund.week_growth,
                "month_growth": fund.month_growth,
                "three_month_growth": fund.three_month_growth,
                "six_month_growth": fund.six_month_growth,
                "year_growth": fund.year_growth,
                "current_year_growth": fund.current_year_growth,
                "manager": fund.manager,
                "last_update": fund.last_update,
                "is_followed": fund.code in followed_codes
            }
            for fund in funds
        ]

    async def search_funds(self, keyword: str, limit: int = 20, page: int = 1, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """专门的搜索基金接口，支持代码和名称模糊匹配，带关注状态。
        Args:
            keyword: 搜索关键词
            limit: 每页数量
            page: 页码
            user_id: 可选的用户ID，用于判断关注状态
        Returns:
            基金列表，包含关注状态
        """
        stmt = select(Fund)

        # 支持代码和名称模糊搜索
        stmt = stmt.where(or_(Fund.code.ilike(f"%{keyword}%"), Fund.name.ilike(f"%{keyword}%")))

        # 优化排序：优先匹配代码精确前缀的，再按名称排序
        stmt = (
            stmt.order_by(Fund.code.ilike(f"{keyword}%").desc(), Fund.name.ilike(f"{keyword}%").desc(), Fund.code)
            .limit(limit)
            .offset((page - 1) * limit)
        )

        result = await self.db.execute(stmt)
        funds = list(result.scalars().all())
        
        # 组装返回结果，包含关注状态
        followed_codes = set()
        if user_id:
            followed_stmt = select(FollowedFund).where(FollowedFund.user_id == user_id)
            followed_result = await self.db.execute(followed_stmt)
            followed_codes = {f.fund_code for f in followed_result.scalars().all()}
        
        return [
            {
                "id": fund.id,
                "code": fund.code,
                "name": fund.name,
                "type": fund.type,
                "nav": fund.nav,
                "acc_nav": fund.acc_nav,
                "day_growth": fund.day_growth,
                "week_growth": fund.week_growth,
                "month_growth": fund.month_growth,
                "three_month_growth": fund.three_month_growth,
                "six_month_growth": fund.six_month_growth,
                "year_growth": fund.year_growth,
                "current_year_growth": fund.current_year_growth,
                "manager": fund.manager,
                "last_update": fund.last_update,
                "is_followed": fund.code in followed_codes
            }
            for fund in funds
        ]

    # ============================================================
    # 自选基金相关
    # ============================================================

    async def get_followed_funds(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户关注的基金列表。"""
        # 查询关注记录
        stmt = select(FollowedFund).where(FollowedFund.user_id == user_id)
        result = await self.db.execute(stmt)
        followed_records = result.scalars().all()

        output = []
        for record in followed_records:
            # 获取基金实时详情
            fund = await self.get_fund_detail(record.fund_code)

            # 组合响应数据
            item = {
                "id": record.id,
                "user_id": record.user_id,
                "fund_code": record.fund_code,
                "remark": record.remark,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "fund_info": fund,
            }
            output.append(item)

        return output

    async def follow_fund(self, user_id: int, fund_code: str, remark: str = None) -> FollowedFund:
        """关注基金。"""
        # 1. 检查基金是否存在
        stmt = select(Fund).where(Fund.code == fund_code)
        result = await self.db.execute(stmt)
        fund = result.scalar_one_or_none()
        if not fund:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="基金不存在")

        # 2. 检查是否已关注
        stmt = select(FollowedFund).where(FollowedFund.user_id == user_id, FollowedFund.fund_code == fund_code)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # 3. 创建关注记录
        new_follow = FollowedFund(user_id=user_id, fund_code=fund_code, remark=remark)
        self.db.add(new_follow)
        await self.db.commit()
        await self.db.refresh(new_follow)
        return new_follow

    async def unfollow_fund(self, user_id: int, fund_code: str) -> bool:
        """取消关注基金。"""
        stmt = select(FollowedFund).where(FollowedFund.user_id == user_id, FollowedFund.fund_code == fund_code)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            await self.db.delete(record)
            await self.db.commit()
            return True
        return False

    async def sync_all_fund_basics(self) -> int:
        """从天天基金同步全量基金基础信息。"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "http://fund.eastmoney.com/",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.get(self.FUND_LIST_URL, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch fund list: {response.status_code}")
                    return 0

                # 解析 JS 文件内容: var r = [["000001","HXCZHH","华夏成长混合","混合型","HUAXIACHENGZHANGHUNHE"],...]
                content = response.text
                match = re.search(r"var\s+r\s*=\s*(\[.*\]);", content)
                if not match:
                    logger.error("Could not parse fund list JS content")
                    return 0

                fund_data = json.loads(match.group(1))
                return await self._batch_save_funds(fund_data)

            except Exception as e:
                logger.exception(f"Error syncing fund basics: {e}")
                return 0

    async def _batch_save_funds(self, fund_items: List[List[str]]) -> int:
        """批量保存基金基础信息入库。"""
        count = 0
        total = len(fund_items)
        logger.info(f"Starting to sync {total} funds...")

        # 为了性能，我们分批处理
        batch_size = 500
        for i in range(0, total, batch_size):
            batch = fund_items[i : i + batch_size]

            for item in batch:
                # item 格式: [代码, 拼音缩写, 名称, 类型, 全拼]
                code, _, name, ftype, _ = item

                # 检查是否存在
                stmt = select(Fund).where(Fund.code == code)
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # 更新可能变化的名称或类型
                    if existing.name != name or existing.type != ftype:
                        existing.name = name
                        existing.type = ftype
                        count += 1
                else:
                    # 新增
                    new_fund = Fund(code=code, name=name, type=ftype)
                    self.db.add(new_fund)
                    count += 1

            await self.db.commit()
            logger.info(f"Processed {min(i + batch_size, total)}/{total} funds...")

        return count
