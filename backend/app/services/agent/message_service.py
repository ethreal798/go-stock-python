"""Message persistence and history loading."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import ChatConversation, ChatMessage as ChatMessageModel
from app.schemas.agent import ChatMessage

from .capability_registry import CapabilityDefinition
from .runtime_model_config_service import RuntimeModelConfig


class MessageService:
    """Save chat messages and load conversation history."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save_user_message(
        self,
        *,
        conversation: ChatConversation,
        content: str,
        capability: CapabilityDefinition,
        model_config: RuntimeModelConfig,
        status: str = "completed",
        extra_metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        """Persist a user message and assign the next message_index."""
        return await self._create_message(
            conversation=conversation,
            role="user",
            content=content,
            capability=capability,
            model_config=model_config,
            status=status,
            extra_metadata=extra_metadata,
        )

    async def save_assistant_message(
        self,
        *,
        conversation: ChatConversation,
        content: str,
        capability: CapabilityDefinition,
        model_config: RuntimeModelConfig,
        status: str = "completed",
        usage: dict[str, Any] | None = None,
        finish_reason: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
        error_message: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        """Persist an assistant message with usage, citations, and tool calls."""
        input_tokens, output_tokens, total_tokens = self._parse_usage(usage)
        return await self._create_message(
            conversation=conversation,
            role="assistant",
            content=content,
            capability=capability,
            model_config=model_config,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            citations=citations,
            error_message=error_message,
            extra_metadata=extra_metadata,
        )

    async def save_tool_message(
        self,
        *,
        conversation: ChatConversation,
        content: str,
        tool_call_id: str,
        capability: CapabilityDefinition | None = None,
        model_config: RuntimeModelConfig | None = None,
        status: str = "completed",
        extra_metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        """Persist a tool result message."""
        return await self._create_message(
            conversation=conversation,
            role="tool",
            content=content,
            capability=capability,
            model_config=model_config,
            status=status,
            tool_call_id=tool_call_id,
            extra_metadata=extra_metadata,
        )

    async def get_history(self, conversation_id: str) -> list[ChatMessage]:
        """Load persisted messages for a conversation."""
        stmt = (
            select(ChatMessageModel)
            .join(ChatConversation, ChatMessageModel.conversation_db_id == ChatConversation.id)
            .where(
                ChatConversation.conversation_id == conversation_id,
                ChatConversation.deleted_at.is_(None),
            )
            .order_by(ChatMessageModel.message_index.asc())
        )
        result = await self.db.execute(stmt)
        return [self._to_schema(message) for message in result.scalars().all()]

    async def _create_message(
        self,
        *,
        conversation: ChatConversation,
        role: str,
        content: str,
        capability: CapabilityDefinition | None = None,
        model_config: RuntimeModelConfig | None = None,
        status: str = "completed",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        finish_reason: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_call_id: str | None = None,
        citations: list[dict[str, Any]] | None = None,
        error_message: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        message = ChatMessageModel(
            message_id=str(uuid.uuid4()),
            conversation_db_id=conversation.id,
            role=role,
            content=content,
            message_index=await self._next_message_index(conversation.id),
            capability=capability.code if capability else None,
            capabilities=capability.capabilities if capability else None,
            execution_engine=capability.execution_engine if capability else None,
            rag_enabled=capability.rag_enabled if capability else False,
            tool_enabled=capability.tool_enabled if capability else False,
            status=status,
            model_config_id=model_config.id if model_config else None,
            model_name=model_config.model if model_config else None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            citations=citations,
            extra_metadata=extra_metadata,
            error_message=error_message,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def _next_message_index(self, conversation_db_id: int) -> int:
        stmt = select(func.max(ChatMessageModel.message_index)).where(
            ChatMessageModel.conversation_db_id == conversation_db_id
        )
        result = await self.db.execute(stmt)
        current_max = result.scalar_one_or_none()
        return 0 if current_max is None else current_max + 1

    @staticmethod
    def _parse_usage(usage: dict[str, Any] | None) -> tuple[int | None, int | None, int | None]:
        if not usage:
            return None, None, None

        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
        total_tokens = usage.get("total_tokens")
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        return input_tokens, output_tokens, total_tokens

    @staticmethod
    def _to_schema(message: ChatMessageModel) -> ChatMessage:
        return ChatMessage(
            message_id=message.message_id,
            role=message.role,
            content=message.content,
            status=message.status,
            capability=message.capability,
            capabilities=message.capabilities or [],
            execution_engine=message.execution_engine,
            model_config_id=message.model_config_id,
            model_name=message.model_name,
            citations=message.citations or [],
            tool_calls=message.tool_calls or [],
            created_at=message.created_at,
        )
