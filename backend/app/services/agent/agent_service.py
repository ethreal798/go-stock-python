"""Top-level AI agent orchestration service."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ChatMessage, ChatRequest, ConversationSummary

from .capability_registry import CapabilityRegistry
from .conversation_service import ConversationService
from .message_service import MessageService
from .runtime_model_config_service import RuntimeModelConfigService
from .stream_service import StreamService

logger = logging.getLogger(__name__)


class AgentService:
    """Coordinate chat requests across model config, conversation, chain, and streaming services."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.capability_registry = CapabilityRegistry()
        self.runtime_model_config_service = RuntimeModelConfigService(db)
        self.conversation_service = ConversationService(db)
        self.message_service = MessageService(db)
        self.stream_service = StreamService()
        self._active_tasks: dict[str, bool] = {}

    async def chat_stream(self, user_id: int, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Streaming chat entrypoint."""
        model_config = await self.runtime_model_config_service.resolve(user_id, request.model_config_id)
        capability = self.capability_registry.resolve(request.capability)
        conversation = await self.conversation_service.get_or_create_conversation(
            user_id=user_id,
            conversation_id=request.conversation_id,
            capability=capability,
            model_config=model_config,
            title=self._build_initial_title(request.message) if not request.conversation_id else None,
        )
        conversation_id = conversation.conversation_id
        user_message = await self.message_service.save_user_message(
            conversation=conversation,
            content=request.message,
            capability=capability,
            model_config=model_config,
        )
        await self.conversation_service.update_after_message(
            conversation,
            capability=capability,
            model_config=model_config,
            message_count_increment=1,
        )
        self._active_tasks[conversation_id] = True
        logger.info("Stream chat request: user=%s conv=%s capability=%s", user_id, conversation_id, capability.code)

        try:
            yield self.stream_service.format_event(
                "metadata",
                {
                    "conversation_id": conversation_id,
                    "user_message_id": user_message.message_id,
                    "capability": capability.code,
                    "capabilities": capability.capabilities,
                    "execution_engine": capability.execution_engine,
                    "rag_enabled": capability.rag_enabled,
                    "tool_enabled": capability.tool_enabled,
                    "model_config_id": model_config.id,
                    "model_name": model_config.model,
                },
            )
            if self._active_tasks.get(conversation_id):
                assistant_content = "[TODO] streaming AI Agent response"
                yield self.stream_service.format_event("delta", {"content": assistant_content})
                assistant_message = await self.message_service.save_assistant_message(
                    conversation=conversation,
                    content=assistant_content,
                    capability=capability,
                    model_config=model_config,
                    finish_reason="stop",
                )
                await self.conversation_service.update_after_message(
                    conversation,
                    capability=capability,
                    model_config=model_config,
                    message_count_increment=1,
                )
                yield self.stream_service.format_event(
                    "done",
                    {
                        "message_id": assistant_message.message_id,
                        "status": assistant_message.status,
                    },
                )
        finally:
            self._active_tasks.pop(conversation_id, None)

    async def abort_chat(self, conversation_id: str) -> bool:
        """Abort an active streaming conversation."""
        if conversation_id in self._active_tasks:
            self._active_tasks[conversation_id] = False
            logger.info("Aborted chat: conv=%s", conversation_id)
            return True
        return False

    async def get_history(self, user_id: int, conversation_id: str) -> list[ChatMessage]:
        """Return conversation messages."""
        await self.conversation_service.get_conversation(user_id=user_id, conversation_id=conversation_id)
        return await self.message_service.get_history(conversation_id)

    async def list_conversations(self, user_id: int, limit: int = 20, offset: int = 0) -> list[ConversationSummary]:
        """Return conversation summaries."""
        return await self.conversation_service.list_conversations(user_id=user_id, limit=limit, offset=offset)

    async def delete_conversation(self, user_id: int, conversation_id: str) -> bool:
        """Soft-delete one conversation."""
        return await self.conversation_service.delete_conversation(user_id=user_id, conversation_id=conversation_id)

    @staticmethod
    def _build_initial_title(message: str) -> str:
        """Build a short provisional title from the first user message."""
        title = " ".join(message.strip().split())
        return title[:40] if title else "New conversation"
