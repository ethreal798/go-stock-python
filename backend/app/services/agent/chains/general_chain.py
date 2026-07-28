"""General chat chain."""

from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.schemas.agent import ChatMessage, ChatRequest


@dataclass
class GeneralChainResult:
    """Final result accumulated from a streamed general chat run."""

    content: str = ""
    model_name: str | None = None
    usage: dict[str, Any] | None = None
    finish_reason: str | None = None


class GeneralChain:
    """Plain LLM chat without RAG or tools."""

    async def astream(
        self,
        *,
        request: ChatRequest,
        llm: BaseChatModel,
        history: list[ChatMessage],
        system_prompt: str,
        should_abort: Callable[[], bool] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream LLM deltas and yield a final result event."""
        messages = self._build_messages(request=request, history=history, system_prompt=system_prompt)
        content_parts: list[str] = []
        model_name: str | None = None
        usage: dict[str, Any] | None = None
        finish_reason: str | None = None

        if should_abort and should_abort():
            yield self._build_terminal_event(
                event_type="aborted",
                content_parts=content_parts,
                model_name=model_name,
                usage=usage,
                finish_reason="abort",
            )
            return

        async for chunk in llm.astream(messages):
            model_name = self._extract_model_name(chunk) or model_name
            chunk_usage = getattr(chunk, "usage_metadata", None)
            if chunk_usage:
                usage = dict(chunk_usage)

            response_metadata = getattr(chunk, "response_metadata", None) or {}
            finish_reason = response_metadata.get("finish_reason") or finish_reason

            if should_abort and should_abort():
                yield self._build_terminal_event(
                    event_type="aborted",
                    content_parts=content_parts,
                    model_name=model_name,
                    usage=usage,
                    finish_reason="abort",
                )
                return

            content = self._normalize_content(getattr(chunk, "content", ""))
            if content:
                content_parts.append(content)
                yield {"type": "delta", "content": content, "model": model_name}

            if should_abort and should_abort():
                yield self._build_terminal_event(
                    event_type="aborted",
                    content_parts=content_parts,
                    model_name=model_name,
                    usage=usage,
                    finish_reason="abort",
                )
                return

        yield self._build_terminal_event(
            event_type="done",
            content_parts=content_parts,
            model_name=model_name,
            usage=usage,
            finish_reason=finish_reason or "stop",
        )

    def _build_messages(
        self,
        *,
        request: ChatRequest,
        history: list[ChatMessage],
        system_prompt: str,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for message in history[-20:]:
            if message.role == "user":
                messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                messages.append(AIMessage(content=message.content))
            elif message.role == "system":
                messages.append(SystemMessage(content=message.content))
        messages.append(HumanMessage(content=request.message))
        return messages

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts)
        return str(content) if content is not None else ""

    @staticmethod
    def _extract_model_name(chunk: Any) -> str | None:
        response_metadata = getattr(chunk, "response_metadata", None) or {}
        return response_metadata.get("model_name") or response_metadata.get("model")

    @staticmethod
    def _build_terminal_event(
        *,
        event_type: str,
        content_parts: list[str],
        model_name: str | None,
        usage: dict[str, Any] | None,
        finish_reason: str,
    ) -> dict[str, Any]:
        return {
            "type": event_type,
            "result": GeneralChainResult(
                content="".join(content_parts),
                model_name=model_name,
                usage=usage,
                finish_reason=finish_reason,
            ),
        }
