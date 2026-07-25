"""Message persistence and history loading."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ChatMessage


class MessageService:
    """Save chat messages and load conversation history."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save_user_message(self) -> None:
        """TODO: Persist a user message and assign message_index."""
        raise NotImplementedError

    async def save_assistant_message(self) -> None:
        """TODO: Persist an assistant message with usage/citations/tool calls."""
        raise NotImplementedError

    async def save_tool_message(self) -> None:
        """TODO: Persist a tool result message."""
        raise NotImplementedError

    async def get_history(self, conversation_id: str) -> list[ChatMessage]:
        """TODO: Load persisted messages for a conversation."""
        _ = conversation_id
        return []
