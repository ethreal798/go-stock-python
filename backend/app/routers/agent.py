"""AI agent routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_user_service, oauth2_scheme
from app.schemas.agent import ChatHistoryResponse, ChatRequest, ConversationSummary
from app.services.agent import AgentService
from app.services.user_service import UserService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Return the authenticated user for agent endpoints."""
    return await user_service.get_current_user(token)


@router.post("/chat", response_class=EventSourceResponse, summary="AI chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> EventSourceResponse:
    """Unified streaming chat endpoint."""
    return EventSourceResponse(
        service.chat_stream(current_user.id, request),
        media_type="text/event-stream",
    )


@router.post("/abort", summary="Abort chat")
async def abort_chat(
    conversation_id: str = Query(..., description="Conversation ID to abort"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    success = await service.abort_chat(conversation_id)
    return {"success": success}


@router.get("/history", response_model=list[ConversationSummary], summary="Conversation list")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> list[ConversationSummary]:
    return await service.list_conversations(current_user.id, limit=limit, offset=offset)


@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse, summary="Conversation history")
async def get_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> ChatHistoryResponse:
    messages = await service.get_history(current_user.id, conversation_id)
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        messages=messages,
    )


@router.delete("/history/{conversation_id}", summary="Delete conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    success = await service.delete_conversation(current_user.id, conversation_id)
    return {"success": success}
