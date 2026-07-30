"""基于 Redis Stream 的 Agent 实时事件发布与断点续读。"""

import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from app.config import settings


class AgentEventStream:
    """封装每个 Run 独立的 Redis Stream。"""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def publish(self, run_id: UUID, event: str, data: dict[str, Any]) -> str:
        """发布事件并返回 Redis 生成的事件 ID。"""
        key = self.key(run_id)
        event_id = await self.redis.xadd(
            key,
            {"event": event, "data": json.dumps(data, ensure_ascii=False)},
            maxlen=settings.AGENT_EVENT_STREAM_MAXLEN,
            approximate=True,
        )
        await self.redis.expire(key, settings.AGENT_EVENT_STREAM_TTL_SECONDS)
        return str(event_id)

    async def read(
        self, run_id: UUID, after_event_id: str, *, block_ms: int | None = None
    ) -> list[tuple[str, str, dict]]:
        """读取 after_event_id 之后的事件；无事件时按配置阻塞等待。"""
        result = await self.redis.xread(
            {self.key(run_id): after_event_id},
            count=100,
            block=block_ms if block_ms is not None else settings.AGENT_STREAM_BLOCK_MS,
        )
        events: list[tuple[str, str, dict]] = []
        for _, entries in result:
            for event_id, fields in entries:
                data = json.loads(fields.get("data") or "{}")
                events.append((str(event_id), fields.get("event") or "message", data))
        return events

    @staticmethod
    def key(run_id: UUID) -> str:
        """生成单个运行任务对应的 Redis Stream Key。"""
        return f"agent:run:{run_id}:events"
