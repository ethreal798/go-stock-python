"""General chat chain."""

from typing import Any

from app.schemas.agent import ChatRequest


class GeneralChain:
    """Plain LLM chat without RAG or tools."""

    async def run(self, request: ChatRequest, context: dict[str, Any]) -> dict[str, Any]:
        """TODO: Build prompt, call LLM, and return assistant output."""
        _ = request
        _ = context
        return {
            "content": "[TODO] general chat response",
            "citations": [],
            "tool_calls": [],
            "usage": None,
        }
