"""News RAG chat chain."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import ChatRequest
from app.services.rag.retrieval_service import RetrievalService


class NewsRagChain:
    """Workflow chain that retrieves news chunks before generating an answer."""

    def __init__(self, db: AsyncSession) -> None:
        self.retrieval_service = RetrievalService(db)

    async def run(self, request: ChatRequest, context: dict[str, Any]) -> dict[str, Any]:
        """TODO: Retrieve news context, call LLM, and return answer with citations."""
        _ = request
        _ = context
        return {
            "content": "[TODO] news RAG response",
            "citations": [],
            "tool_calls": [],
            "usage": None,
        }
