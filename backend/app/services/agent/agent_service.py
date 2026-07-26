"""Top-level AI agent orchestration service."""

import logging
from collections.abc import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ChatMessage, ChatRequest, ConversationSummary

from .capability_registry import CapabilityRegistry
from .chains.general_chain import GeneralChain, GeneralChainResult
from .conversation_service import ConversationService
from .llm_factory import LLMFactory
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
        self.llm_factory = LLMFactory()
        self.general_chain = GeneralChain()
        self._active_tasks: dict[str, bool] = {}

    async def chat_stream(self, user_id: int, request: ChatRequest) -> AsyncGenerator[dict[str, str], None]:
        """Streaming chat entrypoint."""
        capability = self.capability_registry.resolve(request.capability)
        if capability.code != "general":
            yield self.stream_service.format_event("error", {"message": "当前仅支持普通聊天能力"})
            return

        conversation = None
        conversation_id = request.conversation_id or ""
        model_config = None

        try:
            # 1. 解析传入的模型配置
            model_config = await self.runtime_model_config_service.resolve(user_id, request.model_config_id)
            # 2. 实例化 对话模型类
            conversation = await self.conversation_service.get_or_create_conversation(
                user_id=user_id,
                conversation_id=request.conversation_id,
                capability=capability,
                model_config=model_config,
                title=self._build_initial_title(request.message) if not request.conversation_id else None,
            )
            # 3. 获取历史消息， 构建上下文联系
            conversation_id = conversation.conversation_id
            history = await self.message_service.get_history(conversation_id)
            # 4. 用户消息入库存储
            user_message = await self.message_service.save_user_message(
                conversation=conversation,
                content=request.message,
                capability=capability,
                model_config=model_config,
            )
            # 5. 本次对话存储入库
            await self.conversation_service.update_after_message(
                conversation,
                capability=capability,
                model_config=model_config,
                message_count_increment=1,
            )
            self._active_tasks[conversation_id] = True
            logger.info("Stream chat request: user=%s conv=%s capability=%s", user_id, conversation_id, capability.code)

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
                llm = self.llm_factory.create_chat_model(model_config, streaming=True)
                final_result = GeneralChainResult()

                async for event in self.general_chain.astream(request=request, llm=llm, history=history):
                    if event["type"] == "delta":
                        yield self.stream_service.format_event("delta", {"content": event["content"]})
                    elif event["type"] == "done":
                        final_result = event["result"]

                assistant_message = await self._save_successful_assistant_message(
                    conversation=conversation,
                    capability=capability,
                    model_config=model_config,
                    result=final_result,
                )
                yield self.stream_service.format_event(
                    "done",
                    {
                        "message_id": assistant_message.message_id,
                        "status": assistant_message.status,
                        "model_name": assistant_message.model_name,
                        "usage": final_result.usage,
                    },
                )
        except Exception as exc:
            logger.exception("Chat stream failed: user=%s conv=%s", user_id, conversation_id)
            error_message = self._error_message(exc)
            if conversation is not None and model_config is not None:
                failed_message = await self.message_service.save_assistant_message(
                    conversation=conversation,
                    content="",
                    capability=capability,
                    model_config=model_config,
                    status="failed",
                    error_message=error_message,
                    finish_reason="error",
                )
                await self.conversation_service.update_after_message(
                    conversation,
                    capability=capability,
                    model_config=model_config,
                    message_count_increment=1,
                )
                yield self.stream_service.format_event(
                    "error",
                    {
                        "message_id": failed_message.message_id,
                        "status": failed_message.status,
                        "message": error_message,
                    },
                )
            else:
                yield self.stream_service.format_event("error", {"message": error_message})
        finally:
            if conversation_id:
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

    async def _save_successful_assistant_message(
        self,
        *,
        conversation,
        capability,
        model_config,
        result: GeneralChainResult,
    ):
        assistant_message = await self.message_service.save_assistant_message(
            conversation=conversation,
            content=result.content,
            capability=capability,
            model_config=model_config,
            usage=result.usage,
            finish_reason=result.finish_reason,
        )
        if result.model_name and result.model_name != assistant_message.model_name:
            assistant_message.model_name = result.model_name
        await self.conversation_service.update_after_message(
            conversation,
            capability=capability,
            model_config=model_config,
            message_count_increment=1,
            input_tokens=(result.usage or {}).get("input_tokens", (result.usage or {}).get("prompt_tokens", 0)),
            output_tokens=(result.usage or {}).get("output_tokens", (result.usage or {}).get("completion_tokens", 0)),
            total_tokens=(result.usage or {}).get("total_tokens"),
        )
        return assistant_message

    @staticmethod
    def _error_message(exc: Exception) -> str:
        if isinstance(exc, HTTPException):
            return str(exc.detail)
        return str(exc) or "AI 对话生成失败"
