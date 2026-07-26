"""SSE event helpers for chat streaming."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from app.schemas.agent import ChatStreamEvent


class StreamService:
    """Build normalized SSE payloads for the frontend."""

    def format_event(self, event: str, data: dict[str, Any] | None = None) -> dict[str, str]:
        """Format one SSE event."""
        payload = ChatStreamEvent(event=event, data=data or {})
        return {
            "event": payload.event,
            "data": json.dumps(payload.data, ensure_ascii=False),
        }

    async def placeholder_stream(self, content: str) -> AsyncGenerator[dict[str, str], None]:
        """Temporary stream used before real chain streaming is wired."""
        yield self.format_event("delta", {"content": content})
        yield self.format_event("done", {})
