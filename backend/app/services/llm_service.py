"""大模型调用服务。"""

from typing import Any

import httpx

from app.config import settings


class LLMService:
    """OpenAI 兼容 chat completions 调用封装。"""

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """调用聊天模型生成回答。"""
        model_name = model or settings.AI_MODEL_NAME
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": settings.AI_TEMPERATURE if temperature is None else temperature,
            "max_tokens": max_tokens or settings.AI_MAX_TOKENS,
        }
        headers = {"Content-Type": "application/json"}

        if settings.AI_API_KEY:
            headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"

        url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "content": content,
            "model": data.get("model", model_name),
            "usage": data.get("usage"),
        }
