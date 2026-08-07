"""基金业务逻辑服务。"""

import re
import json
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund, FollowedFund

logger = logging.getLogger(__name__)


class FundService:
    """基金服务类"""

    # 天天基金全量列表接口 (包含约 1.5w 只基金)
    FUND_LIST_URL = "http://fund.eastmoney.com/js/fundcode_search.js"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_fund_detail(self, code: str) -> Optional[Fund]:
        """获取基金身份和排行可观测状态。"""
        stmt = select(Fund).where(Fund.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_funds(
        self, keyword: Optional[str] = None, limit: int = 20, page: int = 1, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
                "category": fund.category,
                "status": fund.status,
                "last_seen_data_date": fund.last_seen_data_date,
                "last_seen_at": fund.last_seen_at,
                "is_followed": fund.code in followed_codes,
            }
            for fund in funds
        ]

    async def search_funds(
        self, keyword: str, limit: int = 20, page: int = 1, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
                "category": fund.category,
                "status": fund.status,
                "last_seen_data_date": fund.last_seen_data_date,
                "last_seen_at": fund.last_seen_at,
                "is_followed": fund.code in followed_codes,
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
            logger.debug("Processed %s/%s funds", min(i + batch_size, total), total)

        return count
