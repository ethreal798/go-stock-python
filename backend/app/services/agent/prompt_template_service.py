"""Prompt template loading for agent capabilities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import PromptTemplate


class PromptTemplateService:
    """Load prompt templates with safe fallbacks."""

    GENERAL_CHAT_SYSTEM = "general_chat_system"

    DEFAULT_GENERAL_CHAT_SYSTEM_PROMPT = (
        "你是一个中文 AI 助手，请用清晰、准确、克制的方式回答用户问题。"
        "涉及投资、医疗、法律等高风险内容时，提醒用户这不是专业建议。"
    )

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_type(self, template_type: str, fallback: str = "") -> str:
        """Return the first non-empty template content for a template type."""
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
        """Return the system prompt used by plain general chat."""
        return await self.get_by_type(
            self.GENERAL_CHAT_SYSTEM,
            fallback=self.DEFAULT_GENERAL_CHAT_SYSTEM_PROMPT,
        )
