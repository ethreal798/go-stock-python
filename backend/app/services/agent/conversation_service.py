"""Conversation persistence operations."""

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import ChatConversation
from app.schemas.agent import ConversationSummary

from .capability_registry import CapabilityDefinition
from .runtime_model_config_service import RuntimeModelConfig


class ConversationService:
    """Create, load, list, update, and soft-delete chat conversations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_conversation(
        self,
        *,
        user_id: int,
        conversation_id: str | None,
        capability: CapabilityDefinition,
        model_config: RuntimeModelConfig,
        title: str | None = None,
    ) -> ChatConversation:
        """Load an existing conversation owned by the user or create a new one."""
        if conversation_id:
            conversation = await self.get_conversation(user_id=user_id, conversation_id=conversation_id)
            self._apply_latest_runtime(conversation, capability=capability, model_config=model_config)
            await self.db.flush()
            return conversation

        conversation = ChatConversation(
            conversation_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            capability=capability.code,
            execution_engine=capability.execution_engine,
            rag_enabled=capability.rag_enabled,
            tool_enabled=capability.tool_enabled,
            model_config_id=model_config.id,
            model_name=model_config.model,
            message_count=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_conversation(self, *, user_id: int, conversation_id: str) -> ChatConversation:
        """Return one active conversation owned by the user."""
        stmt = select(ChatConversation).where(
            ChatConversation.conversation_id == conversation_id,
            ChatConversation.user_id == user_id,
            ChatConversation.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
        return conversation

    async def list_conversations(self, *, user_id: int, limit: int = 20, offset: int = 0) -> list[ConversationSummary]:
        """Return conversation summaries for the current user."""
        stmt = (
            select(ChatConversation)
            .where(ChatConversation.user_id == user_id, ChatConversation.deleted_at.is_(None))
            .order_by(
                desc(ChatConversation.last_message_at).nullslast(),
                desc(ChatConversation.updated_at).nullslast(),
                desc(ChatConversation.id),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [self._to_summary(conversation) for conversation in result.scalars().all()]

    async def delete_conversation(self, *, user_id: int, conversation_id: str) -> bool:
        """Soft-delete a conversation owned by the current user."""
        conversation = await self.get_conversation(user_id=user_id, conversation_id=conversation_id)
        conversation.deleted_at = datetime.now()
        await self.db.flush()
        return True

    async def update_after_message(
        self,
        conversation: ChatConversation,
        *,
        capability: CapabilityDefinition | None = None,
        model_config: RuntimeModelConfig | None = None,
        message_count_increment: int = 1,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int | None = None,
        last_message_at: datetime | None = None,
    ) -> ChatConversation:
        """Refresh conversation summary fields after one persisted message."""
        if capability is not None and model_config is not None:
            self._apply_latest_runtime(conversation, capability=capability, model_config=model_config)
        elif capability is not None:
            conversation.capability = capability.code
            conversation.execution_engine = capability.execution_engine
            conversation.rag_enabled = capability.rag_enabled
            conversation.tool_enabled = capability.tool_enabled
        elif model_config is not None:
            conversation.model_config_id = model_config.id
            conversation.model_name = model_config.model

        conversation.message_count = (conversation.message_count or 0) + message_count_increment
        conversation.total_input_tokens = (conversation.total_input_tokens or 0) + (input_tokens or 0)
        conversation.total_output_tokens = (conversation.total_output_tokens or 0) + (output_tokens or 0)
        conversation.total_tokens = (conversation.total_tokens or 0) + (
            total_tokens if total_tokens is not None else (input_tokens or 0) + (output_tokens or 0)
        )
        conversation.last_message_at = last_message_at or datetime.now()
        await self.db.flush()
        return conversation

    @staticmethod
    def _apply_latest_runtime(
        conversation: ChatConversation,
        *,
        capability: CapabilityDefinition,
        model_config: RuntimeModelConfig,
    ) -> None:
        conversation.capability = capability.code
        conversation.execution_engine = capability.execution_engine
        conversation.rag_enabled = capability.rag_enabled
        conversation.tool_enabled = capability.tool_enabled
        conversation.model_config_id = model_config.id
        conversation.model_name = model_config.model

    @staticmethod
    def _to_summary(conversation: ChatConversation) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=conversation.conversation_id,
            title=conversation.title or "",
            capability=conversation.capability,
            execution_engine=conversation.execution_engine,
            model_config_id=conversation.model_config_id,
            model_name=conversation.model_name,
            message_count=conversation.message_count or 0,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
