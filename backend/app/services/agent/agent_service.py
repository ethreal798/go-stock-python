"""Top-level AI agent orchestration service."""

import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ChatMessage, ChatRequest, ChatResponse, ConversationSummary

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

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Non-streaming chat entrypoint.

        TODO: Resolve user model config, get/create conversation, save messages,
        execute the resolved chain, then persist and return the assistant message.
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())
        capability = self.capability_registry.resolve(request.capability)
        logger.info(
            "Chat request: conv=%s capability=%s model_config_id=%s",
            conversation_id,
            capability.code,
            request.model_config_id,
        )

        response_message = ChatMessage(
            message_id=str(uuid.uuid4()),
            role="assistant",
            content="[TODO] AI Agent response placeholder",
            capability=capability.code,
            capabilities=capability.capabilities,
            execution_engine=capability.execution_engine,
            model_config_id=request.model_config_id,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=response_message,
            capability=capability.code,
            capabilities=capability.capabilities,
            execution_engine=capability.execution_engine,
            rag_enabled=capability.rag_enabled,
            tool_enabled=capability.tool_enabled,
            model_config_id=request.model_config_id,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Streaming chat entrypoint."""
        conversation_id = request.conversation_id or str(uuid.uuid4())
        capability = self.capability_registry.resolve(request.capability)
        self._active_tasks[conversation_id] = True
        logger.info("Stream chat request: conv=%s capability=%s", conversation_id, capability.code)

        try:
            yield self.stream_service.format_event(
                "metadata",
                {
                    "conversation_id": conversation_id,
                    "capability": capability.code,
                    "capabilities": capability.capabilities,
                    "execution_engine": capability.execution_engine,
                    "rag_enabled": capability.rag_enabled,
                    "tool_enabled": capability.tool_enabled,
                    "model_config_id": request.model_config_id,
                },
            )
            if self._active_tasks.get(conversation_id):
                async for chunk in self.stream_service.placeholder_stream("[TODO] streaming AI Agent response"):
                    yield chunk
        finally:
            self._active_tasks.pop(conversation_id, None)

    async def abort_chat(self, conversation_id: str) -> bool:
        """Abort an active streaming conversation."""
        if conversation_id in self._active_tasks:
            self._active_tasks[conversation_id] = False
            logger.info("Aborted chat: conv=%s", conversation_id)
            return True
        return False

    async def get_history(self, conversation_id: str) -> list[ChatMessage]:
        """Return conversation messages."""
        return await self.message_service.get_history(conversation_id)

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> list[ConversationSummary]:
        """Return conversation summaries."""
        return await self.conversation_service.list_conversations(limit=limit, offset=offset)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Soft-delete one conversation."""
        return await self.conversation_service.delete_conversation(conversation_id)
