"""AI Agent 服务。

负责管理 AI 模型调用、工具注册、对话历史等。
"""

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.agent import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationSummary,
)

logger = logging.getLogger(__name__)


class AgentService:
    """AI Agent 服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # 当前活跃的对话任务，用于支持 abort
        self._active_tasks: dict[str, bool] = {}

    # ----------------------------------------------------------
    # 聊天核心
    # ----------------------------------------------------------

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天。

        Args:
            request: 聊天请求
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())
        # TODO: 加载对话历史 -> 构建 prompt -> 调用 LLM -> 保存对话 -> 返回
        logger.info("Chat request: conv=%s, model=%s", conversation_id, request.model)

        response_message = ChatMessage(
            role="assistant",
            content="[TODO] AI Agent 响应占位",
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=response_message,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """流式聊天（SSE）。

        Args:
            request: 聊天请求

        Yields:
            SSE 格式的文本片段
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())
        self._active_tasks[conversation_id] = True
        logger.info("Stream chat request: conv=%s", conversation_id)

        try:
            # TODO: 实现 LLM 流式调用
            # 伪代码结构:
            # async for chunk in llm.astream(messages):
            #     if not self._active_tasks.get(conversation_id):
            #         break
            #     yield f"data: {json.dumps({'content': chunk})}\n\n"
            placeholder = "[TODO] 流式 AI Agent 响应占位"
            yield f"data: {placeholder}\n\n"
        finally:
            self._active_tasks.pop(conversation_id, None)

    # ----------------------------------------------------------
    # 对话控制
    # ----------------------------------------------------------

    async def abort_chat(self, conversation_id: str) -> bool:
        """中断正在进行的对话。"""
        if conversation_id in self._active_tasks:
            self._active_tasks[conversation_id] = False
            logger.info("Aborted chat: conv=%s", conversation_id)
            return True
        return False

    # ----------------------------------------------------------
    # 对话历史
    # ----------------------------------------------------------

    async def get_history(self, conversation_id: str) -> list[ChatMessage]:
        """获取对话历史。"""
        # TODO: 从数据库查询
        logger.info("Getting history: conv=%s", conversation_id)
        return []

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> list[ConversationSummary]:
        """列出所有会话摘要。"""
        # TODO: 从数据库查询
        logger.info("Listing conversations: limit=%d, offset=%d", limit, offset)
        return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除会话。"""
        # TODO: 从数据库删除
        logger.info("Deleting conversation: conv=%s", conversation_id)
        return True
