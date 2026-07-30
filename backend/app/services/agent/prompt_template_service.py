"""加载 Agent 提示词模板，并在模板缺失时提供默认值。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import PromptTemplate


class PromptTemplateService:
    """从数据库读取提示词模板。"""

    GENERAL_CHAT_SYSTEM = "general_chat_system"

    DEFAULT_GENERAL_CHAT_SYSTEM_PROMPT = (
        "你是一个中文 AI 助手，请用清晰、准确、克制的方式回答用户问题。"
        "涉及投资、医疗、法律等高风险内容时，提醒用户这不是专业建议。"
    )

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_type(self, template_type: str, fallback: str = "") -> str:
        """返回指定类型最新的非空模板，不存在时返回 fallback。"""
        stmt = (
            select(PromptTemplate.content)
            .where(PromptTemplate.type == template_type)
            .order_by(PromptTemplate.updated_at.desc(), PromptTemplate.id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        if content and content.strip():
            return content
        return fallback

    async def get_general_chat_system_prompt(self) -> str:
        """返回普通聊天使用的系统提示词。"""
        return await self.get_by_type(
            self.GENERAL_CHAT_SYSTEM,
            fallback=self.DEFAULT_GENERAL_CHAT_SYSTEM_PROMPT,
        )
