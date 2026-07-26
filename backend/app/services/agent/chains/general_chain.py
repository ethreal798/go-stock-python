"""General chat chain."""

from collections.abc import AsyncGenerator
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

    system_prompt = (
        "你是一个中文 AI 助手，请用清晰、准确、克制的方式回答用户问题。"
        "涉及投资、医疗、法律等高风险内容时，提醒用户这不是专业建议。"
    )

    async def astream(
        self,
        *,
        request: ChatRequest,
        llm: BaseChatModel,
        history: list[ChatMessage],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream LLM deltas and yield a final result event."""
        messages = self._build_messages(request=request, history=history)
        content_parts: list[str] = []
        model_name: str | None = None
        usage: dict[str, Any] | None = None
        finish_reason: str | None = None

        async for chunk in llm.astream(messages):
            model_name = self._extract_model_name(chunk) or model_name
            chunk_usage = getattr(chunk, "usage_metadata", None)
            if chunk_usage:
                usage = dict(chunk_usage)

            response_metadata = getattr(chunk, "response_metadata", None) or {}
            finish_reason = response_metadata.get("finish_reason") or finish_reason

            content = self._normalize_content(getattr(chunk, "content", ""))
            if content:
                content_parts.append(content)
                yield {"type": "delta", "content": content, "model": model_name}

        yield {
            "type": "done",
            "result": GeneralChainResult(
                content="".join(content_parts),
                model_name=model_name,
                usage=usage,
                finish_reason=finish_reason or "stop",
            ),
        }

    def _build_messages(self, *, request: ChatRequest, history: list[ChatMessage]) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=self.system_prompt)]
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
