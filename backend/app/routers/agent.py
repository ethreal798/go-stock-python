"""AI Agent 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.schemas.agent import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ConversationSummary,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db)


@router.post("/chat", summary="AI 聊天")
async def chat(
    request: ChatRequest,
    service: AgentService = Depends(get_agent_service),
):
    """与 AI Agent 对话。当 request.stream=True 时返回 SSE 流式响应。"""
    if request.stream:
        return EventSourceResponse(
            service.chat_stream(request),
            media_type="text/event-stream",
        )
    else:
        return await service.chat(request)


@router.post("/abort", summary="中断对话")
async def abort_chat(
    conversation_id: str = Query(..., description="要中断的会话ID"),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    """中断正在进行的 AI 对话。"""
    success = await service.abort_chat(conversation_id)
    return {"success": success}


@router.get("/history", response_model=list[ConversationSummary], summary="会话列表")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AgentService = Depends(get_agent_service),
) -> list[ConversationSummary]:
    """获取所有对话会话列表。"""
    return await service.list_conversations(limit=limit, offset=offset)


@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse, summary="对话历史")
async def get_chat_history(
    conversation_id: str,
    service: AgentService = Depends(get_agent_service),
) -> ChatHistoryResponse:
    """获取指定会话的完整对话历史。"""
    messages = await service.get_history(conversation_id)
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        messages=messages,
    )


@router.delete("/history/{conversation_id}", summary="删除会话")
async def delete_conversation(
    conversation_id: str,
    service: AgentService = Depends(get_agent_service),
) -> dict:
    """删除指定会话及其历史记录。"""
    success = await service.delete_conversation(conversation_id)
    return {"success": success}
