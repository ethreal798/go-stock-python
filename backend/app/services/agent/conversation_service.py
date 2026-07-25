"""Conversation persistence operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ConversationSummary


class ConversationService:
    """Create, load, list, update, and soft-delete chat conversations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_conversation(self) -> None:
        """TODO: Load an existing conversation or create a new one."""
        raise NotImplementedError

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> list[ConversationSummary]:
        """TODO: Return conversation summaries for the current user."""
        return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """TODO: Soft-delete a conversation."""
        return True

    async def update_after_message(self) -> None:
        """TODO: Refresh counters, token totals, model info, and last_message_at."""
        raise NotImplementedError
