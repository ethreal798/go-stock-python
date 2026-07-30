"""独立执行 LangGraph Agent 后台任务的 Worker 进程。
    python -m app.workers.agent_run_worker
"""

import asyncio
import logging
import os
import socket
import sys
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select, update

from app.config import settings
from app.core.database import async_session_factory, close_db
from app.core.redis import close_redis, get_redis
from app.models.agent import AgentMessage, AgentRun, AgentThread
from app.services.agent.llm_factory import LLMFactory
from app.services.agent.prompt_template_service import PromptTemplateService
from app.services.agent.runtime_model_config_service import RuntimeModelConfigService
from app.services.agent.event_stream import AgentEventStream
from app.services.agent.graph import build_general_chat_graph
from app.services.agent.agent_service import claim_next_run

logger = logging.getLogger(__name__)


class AgentRunWorker:
    """轮询、执行并持久化 Agent Run，且不依赖客户端 SSE 连接。"""

    def __init__(self) -> None:
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}"
        self.llm_factory = LLMFactory()
        self._stopping = False

    async def run_forever(self) -> None:
        """初始化 Checkpointer，并持续领取数据库中的待执行任务。"""
        await self._interrupt_stale_runs()
        checkpoint_url = self._checkpoint_url()
        async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as checkpointer:
            await checkpointer.setup()
            logger.info("Agent worker started: worker_id=%s", self.worker_id)
            last_reap_at = time.monotonic()
            while not self._stopping:
                if time.monotonic() - last_reap_at >= min(settings.AGENT_RUN_LEASE_SECONDS / 2, 30):
                    await self._interrupt_stale_runs()
                    last_reap_at = time.monotonic()
                run_id = await self._claim()
                if run_id is None:
                    await asyncio.sleep(settings.AGENT_RUN_POLL_SECONDS)
                    continue
                await self._execute(run_id, checkpointer)

    async def _claim(self) -> UUID | None:
        """在独立事务中原子领取一个待执行任务。"""
        async with async_session_factory() as db:
            async with db.begin():
                run = await claim_next_run(db, self.worker_id)
                return run.id if run is not None else None

    async def _execute(self, run_id: UUID, checkpointer: AsyncPostgresSaver) -> None:
        """执行单个 Run，并同步写入 Redis 事件和 PostgreSQL 快照。"""
        redis = await get_redis()
        events = AgentEventStream(redis)
        content_parts: list[str] = []
        usage: dict[str, Any] | None = None
        model_name: str | None = None
        finish_reason: str | None = None
        last_event_id: str | None = None
        last_snapshot_at = time.monotonic()

        try:
            # 模型配置和提示词只在任务开始时读取一次，随后释放数据库连接。
            async with async_session_factory() as db:
                run = (await db.execute(select(AgentRun).where(AgentRun.id == run_id))).scalar_one()
                user_message = (
                    await db.execute(select(AgentMessage).where(AgentMessage.id == run.user_message_id))
                ).scalar_one()
                model_config = await RuntimeModelConfigService(db).resolve(run.user_id, run.model_config_id)
                system_prompt = await PromptTemplateService(db).get_general_chat_system_prompt()

            llm = self.llm_factory.create_chat_model(model_config, streaming=True)
            graph = build_general_chat_graph(llm=llm, system_prompt=system_prompt, checkpointer=checkpointer)
            config = {
                "configurable": {
                    "thread_id": str(run.thread_id),
                    "run_id": str(run.id),
                    "user_id": str(run.user_id),
                    "model_config_id": run.model_config_id,
                }
            }
            await events.publish(run_id, "metadata", {"run_id": str(run_id), "status": "running"})

            # LangGraph 负责模型调用和 Checkpoint，Worker 负责业务快照与实时事件。
            async for chunk, _metadata in graph.astream(
                {"messages": [HumanMessage(content=user_message.content)]},
                config=config,
                stream_mode="messages",
            ):
                model_name = self._extract_model_name(chunk) or model_name
                chunk_usage = getattr(chunk, "usage_metadata", None)
                if chunk_usage:
                    usage = dict(chunk_usage)
                response_metadata = getattr(chunk, "response_metadata", None) or {}
                finish_reason = response_metadata.get("finish_reason") or finish_reason

                content = self._normalize_content(getattr(chunk, "content", ""))
                if content:
                    content_parts.append(content)
                    last_event_id = await events.publish(run_id, "delta", {"content": content})

                now = time.monotonic()
                if now - last_snapshot_at >= settings.AGENT_SNAPSHOT_INTERVAL_SECONDS:
                    # 周期性快照既用于刷新恢复，也用于续租和感知中断请求。
                    canceled = await self._save_progress(run_id, "".join(content_parts), last_event_id)
                    last_snapshot_at = now
                    if canceled:
                        await self._finish_canceled(run_id, "".join(content_parts), last_event_id)
                        terminal_id = await events.publish(
                            run_id, "aborted", {"run_id": str(run_id), "status": "canceled"}
                        )
                        await self._store_terminal_event_id(run_id, terminal_id)
                        return

            content = "".join(content_parts)
            final_status = await self._finish_completed(
                run_id,
                content=content,
                last_event_id=last_event_id,
                usage=usage,
                model_name=model_name or model_config.model,
                finish_reason=finish_reason or "stop",
            )
            terminal_event = "aborted" if final_status == "canceled" else "done"
            terminal_id = await events.publish(
                run_id,
                terminal_event,
                {
                    "run_id": str(run_id),
                    "status": final_status,
                    "model_name": model_name or model_config.model,
                    "usage": usage,
                },
            )
            await self._store_terminal_event_id(run_id, terminal_id)
        except Exception as exc:
            logger.exception("Agent run failed: run_id=%s", run_id)
            await self._finish_failed(run_id, "".join(content_parts), last_event_id, str(exc) or "Agent run failed")
            try:
                event_id = await events.publish(
                    run_id,
                    "error",
                    {"run_id": str(run_id), "status": "failed", "message": str(exc) or "Agent run failed"},
                )
                await self._store_terminal_event_id(run_id, event_id)
            except Exception:
                logger.exception("Failed to publish terminal error event: run_id=%s", run_id)

    async def _save_progress(self, run_id: UUID, content: str, last_event_id: str | None) -> bool:
        """保存部分回复、刷新 Worker 租约，并返回是否收到中断请求。"""
        async with async_session_factory() as db:
            async with db.begin():
                run = (await db.execute(select(AgentRun).where(AgentRun.id == run_id).with_for_update())).scalar_one()
                run.content_snapshot = content
                run.last_event_id = last_event_id or run.last_event_id
                run.lease_expires_at = datetime.now() + timedelta(seconds=settings.AGENT_RUN_LEASE_SECONDS)
                message = (
                    await db.execute(select(AgentMessage).where(AgentMessage.id == run.assistant_message_id))
                ).scalar_one()
                message.content = content
                return run.status == "cancel_requested"

    async def _finish_completed(
        self,
        run_id: UUID,
        *,
        content: str,
        last_event_id: str | None,
        usage: dict[str, Any] | None,
        model_name: str,
        finish_reason: str,
    ) -> str:
        """在同一事务中完成 Run、助手消息和会话 Token 统计。"""
        input_tokens, output_tokens, total_tokens = self._parse_usage(usage)
        async with async_session_factory() as db:
            async with db.begin():
                run = (await db.execute(select(AgentRun).where(AgentRun.id == run_id).with_for_update())).scalar_one()
                if run.status == "cancel_requested":
                    await self._apply_canceled(db, run, content, last_event_id)
                    return "canceled"
                run.status = "completed"
                run.content_snapshot = content
                run.last_event_id = last_event_id or run.last_event_id
                run.model_name = model_name
                run.finish_reason = finish_reason
                run.input_tokens = input_tokens
                run.output_tokens = output_tokens
                run.total_tokens = total_tokens
                run.finished_at = datetime.now()
                run.lease_expires_at = None
                message = (
                    await db.execute(select(AgentMessage).where(AgentMessage.id == run.assistant_message_id))
                ).scalar_one()
                message.content = content
                message.status = "completed"
                message.model_name = model_name
                message.finish_reason = finish_reason
                message.input_tokens = input_tokens
                message.output_tokens = output_tokens
                message.total_tokens = total_tokens
                thread = (
                    await db.execute(select(AgentThread).where(AgentThread.id == run.thread_id).with_for_update())
                ).scalar_one()
                thread.total_input_tokens = (thread.total_input_tokens or 0) + (input_tokens or 0)
                thread.total_output_tokens = (thread.total_output_tokens or 0) + (output_tokens or 0)
                thread.last_message_at = datetime.now()
                return "completed"

    async def _finish_canceled(self, run_id: UUID, content: str, last_event_id: str | None) -> None:
        """持久化任务已取消状态。"""
        async with async_session_factory() as db:
            async with db.begin():
                run = (await db.execute(select(AgentRun).where(AgentRun.id == run_id).with_for_update())).scalar_one()
                await self._apply_canceled(db, run, content, last_event_id)

    async def _apply_canceled(self, db, run: AgentRun, content: str, last_event_id: str | None) -> None:
        """把取消状态同时应用到 Run 和助手消息。"""
        run.status = "canceled"
        run.content_snapshot = content
        run.last_event_id = last_event_id or run.last_event_id
        run.finish_reason = "abort"
        run.finished_at = datetime.now()
        run.lease_expires_at = None
        message = (
            await db.execute(select(AgentMessage).where(AgentMessage.id == run.assistant_message_id))
        ).scalar_one()
        message.content = content
        message.status = "canceled"
        message.finish_reason = "abort"

    async def _finish_failed(
        self,
        run_id: UUID,
        content: str,
        last_event_id: str | None,
        error_message: str,
    ) -> None:
        """持久化任务失败信息和已经生成的部分内容。"""
        async with async_session_factory() as db:
            async with db.begin():
                run = (
                    await db.execute(select(AgentRun).where(AgentRun.id == run_id).with_for_update())
                ).scalar_one_or_none()
                if run is None or run.status in ("completed", "canceled"):
                    return
                run.status = "failed"
                run.content_snapshot = content
                run.last_event_id = last_event_id or run.last_event_id
                run.finish_reason = "error"
                run.error_message = error_message
                run.finished_at = datetime.now()
                run.lease_expires_at = None
                message = (
                    await db.execute(select(AgentMessage).where(AgentMessage.id == run.assistant_message_id))
                ).scalar_one()
                message.content = content
                message.status = "failed"
                message.finish_reason = "error"
                message.error_message = error_message

    async def _store_terminal_event_id(self, run_id: UUID, event_id: str) -> None:
        """保存终态事件 ID，供 SSE 重连时建立游标。"""
        async with async_session_factory() as db:
            async with db.begin():
                await db.execute(update(AgentRun).where(AgentRun.id == run_id).values(last_event_id=event_id))

    async def _interrupt_stale_runs(self) -> None:
        """把租约过期的运行中任务标记为 interrupted，避免静默卡死。"""
        now = datetime.now()
        async with async_session_factory() as db:
            async with db.begin():
                stale = (
                    (
                        await db.execute(
                            select(AgentRun).where(
                                AgentRun.status.in_(("running", "cancel_requested")),
                                AgentRun.lease_expires_at.is_not(None),
                                AgentRun.lease_expires_at < now,
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                for run in stale:
                    run.status = "interrupted"
                    run.finish_reason = "worker_restart"
                    run.error_message = "Agent worker stopped before the run completed"
                    run.finished_at = now
                    run.lease_expires_at = None
                    message = (
                        await db.execute(select(AgentMessage).where(AgentMessage.id == run.assistant_message_id))
                    ).scalar_one()
                    message.status = "failed"
                    message.error_message = run.error_message

    @staticmethod
    def _checkpoint_url() -> str:
        """把 SQLAlchemy PostgreSQL URL 转换为 psycopg 可识别的连接串。"""
        url = settings.LANGGRAPH_DATABASE_URL or settings.DATABASE_URL
        return url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

    @staticmethod
    def _normalize_content(content: Any) -> str:
        """兼容字符串和多模态内容块，提取可展示文本。"""
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
        """从不同兼容服务的响应元数据中提取模型名称。"""
        metadata = getattr(chunk, "response_metadata", None) or {}
        return metadata.get("model_name") or metadata.get("model")

    @staticmethod
    def _parse_usage(usage: dict[str, Any] | None) -> tuple[int | None, int | None, int | None]:
        """兼容 LangChain 与 OpenAI 风格的 Token 用量字段。"""
        if not usage:
            return None, None, None
        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
        total_tokens = usage.get("total_tokens")
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        return input_tokens, output_tokens, total_tokens


async def main() -> None:
    """启动 Worker，并在退出时释放 Redis 和数据库连接。"""
    logging.basicConfig(level=logging.INFO)
    worker = AgentRunWorker()
    try:
        await worker.run_forever()
    finally:
        await close_redis()
        await close_db()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
