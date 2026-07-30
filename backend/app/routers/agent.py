"""LangGraph Agent 的会话、运行任务、流式续传和中断接口。"""

import json
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.core.database import async_session_factory, get_db
from app.core.redis import get_redis
from app.models.agent import AgentRun
from app.models.user import User
from app.routers.auth import get_user_service, oauth2_scheme
from app.schemas.agent import (
    AgentMessageResponse,
    AgentRunAbortResponse,
    AgentRunResponse,
    AgentRunSubmit,
    AgentRunSubmitResponse,
    AgentThreadDeleteResponse,
    AgentThreadResponse,
)
from app.services.agent.agent_service import AgentService, TERMINAL_RUN_STATUSES
from app.services.agent.event_stream import AgentEventStream
from app.services.user_service import UserService

router = APIRouter(prefix="/agent", tags=["AI 智能体"])


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """创建绑定当前数据库会话的 AgentService。"""
    return AgentService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """解析访问令牌并返回当前用户。"""
    return await user_service.get_current_user(token)


@router.get(
    "/threads",
    response_model=list[AgentThreadResponse],
    summary="获取 Agent 会话列表",
    description="按最后消息时间倒序返回当前用户的有效会话。",
)
async def list_threads(
    count: int = Query(20, ge=1, le=100, description="本次返回数量，最大 100"),
    page: int = Query(0, ge=0, description="偏移记录数，从 0 开始"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> list[AgentThreadResponse]:
    """返回当前用户的 Agent 会话列表。"""
    return await service.list_threads(current_user.id, limit=count, offset=page)


@router.delete(
    "/threads/{thread_id}",
    response_model=AgentThreadDeleteResponse,
    summary="删除 Agent 会话",
    description=(
        "软删除指定会话。删除时若存在等待执行的任务则立即取消；" "若任务正在生成，则请求 Worker 在保存当前回复后中断。"
    ),
)
async def delete_thread(
    thread_id: UUID = Path(..., description="Agent 会话 ID"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> AgentThreadDeleteResponse:
    """删除会话，并停止该会话中可能存在的活动任务。"""
    active_run = await service.delete_thread(current_user.id, thread_id)
    await service.db.commit()
    if active_run is not None and active_run.status == "canceled":
        await _publish_aborted_event(active_run, service)
    return AgentThreadDeleteResponse(
        thread_id=thread_id,
        active_run_id=active_run.id if active_run is not None else None,
        run_status=active_run.status if active_run is not None else None,
    )


@router.get(
    "/threads/{thread_id}/messages",
    response_model=list[AgentMessageResponse],
    summary="获取会话消息",
    description="按消息顺序返回指定会话中对用户可见的全部消息。",
)
async def list_thread_messages(
    thread_id: UUID = Path(..., description="Agent 会话 ID"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> list[AgentMessageResponse]:
    """返回指定会话的持久化消息。"""
    return await service.list_messages(current_user.id, thread_id)


@router.post(
    "/runs",
    response_model=AgentRunSubmitResponse,
    status_code=202,
    summary="提交消息并创建 Agent 任务",
    description=(
        "提交用户消息并创建后台运行任务。thread_id 为空时自动创建会话；"
        "相同 client_request_id 会返回原任务，不会重复调用模型。"
    ),
)
async def submit_run(
    request: AgentRunSubmit,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> AgentRunSubmitResponse:
    """聚合创建会话与运行任务，并返回 SSE 订阅地址。"""
    run = await service.submit_run(current_user.id, request)
    return AgentRunSubmitResponse(
        **run.model_dump(),
        stream_url=f"{settings.API_PREFIX}/agent/runs/{run.run_id}/stream",
    )


@router.get(
    "/threads/{thread_id}/active-run",
    response_model=AgentRunResponse | None,
    summary="获取会话的活动任务",
    description="查询会话中处于等待、执行中或等待中断状态的任务；没有活动任务时返回 null。",
)
async def get_active_run(
    thread_id: UUID = Path(..., description="Agent 会话 ID"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> AgentRunResponse | None:
    """返回指定会话当前唯一的活动任务。"""
    await service.get_thread(current_user.id, thread_id)
    run = await service.get_active_run(current_user.id, thread_id)
    return service.to_run_response(run) if run is not None else None


# @router.get(
#     "/runs/{run_id}",
#     response_model=AgentRunResponse,
#     summary="获取 Agent 任务状态",
#     description="从 PostgreSQL 查询任务状态、回复快照、Token 用量和错误信息。",
# )
# async def get_run(
#     run_id: UUID = Path(..., description="Agent 运行任务 ID"),
#     current_user: User = Depends(get_current_user),
#     service: AgentService = Depends(get_agent_service),
# ) -> AgentRunResponse:
#     """返回指定运行任务的持久化状态。"""
#     return await service.get_run_response(current_user.id, run_id)


@router.get(
    "/runs/{run_id}/stream",
    response_class=EventSourceResponse,
    summary="订阅 Agent 任务流",
    description=(
        "通过 SSE 返回 snapshot、metadata、delta、done、aborted 或 error 事件。"
        "刷新后可携带 after_event_id 继续读取 Redis Stream 中尚未消费的事件。"
    ),
)
async def stream_run(
    run_id: UUID = Path(..., description="Agent 运行任务 ID"),
    after_event_id: str | None = Query(None, max_length=64, description="客户端已处理的最后一个事件 ID"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> EventSourceResponse:
    """先返回数据库快照，再持续转发 Redis Stream 事件。"""
    await service.get_run(current_user.id, run_id)
    return EventSourceResponse(
        _run_event_generator(current_user.id, run_id, after_event_id),
        media_type="text/event-stream",
        ping=15,
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/runs/{run_id}/abort",
    response_model=AgentRunAbortResponse,
    summary="中断 Agent 任务",
    description="请求停止指定任务。等待中的任务立即取消，执行中的任务由 Worker 在下一个快照周期停止。",
)
async def abort_run(
    run_id: UUID = Path(..., description="Agent 运行任务 ID"),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> AgentRunAbortResponse:
    """记录中断请求，并在可立即取消时发布 aborted 事件。"""
    run = await service.request_abort(current_user.id, run_id)
    await service.db.commit()
    if run.status == "canceled":
        await _publish_aborted_event(run, service)
    return AgentRunAbortResponse(run_id=run.id, status=run.status)


async def _publish_aborted_event(run: AgentRun, service: AgentService) -> None:
    """发布立即取消事件，并保存终态事件游标。"""
    events = AgentEventStream(await get_redis())
    event_id = await events.publish(run.id, "aborted", {"run_id": str(run.id), "status": "canceled"})
    run.last_event_id = event_id
    await service.db.commit()


async def _run_event_generator(
    user_id: int,
    run_id: UUID,
    after_event_id: str | None,
) -> AsyncGenerator[dict[str, str], None]:
    """生成可续传的 SSE 事件序列。"""
    event_stream = AgentEventStream(await get_redis())
    async with async_session_factory() as db:
        run = await AgentService(db).get_run(user_id, run_id)
        cursor = run.last_event_id or after_event_id or "0-0"
        snapshot = {
            "run_id": str(run.id),
            "thread_id": str(run.thread_id),
            "message_id": str(run.assistant_message_id),
            "content": run.content_snapshot,
            "status": run.status,
            "last_event_id": run.last_event_id,
        }
        yield _sse("snapshot", snapshot, run.last_event_id)
        if run.status in TERMINAL_RUN_STATUSES:
            event = {"completed": "done", "canceled": "aborted"}.get(run.status, "error")
            yield _sse(
                event,
                {"run_id": str(run.id), "status": run.status, "message": run.error_message},
                run.last_event_id,
            )
            return

    while True:
        entries = await event_stream.read(run_id, cursor)
        for event_id, event, data in entries:
            cursor = event_id
            yield _sse(event, data, event_id)
            if event in ("done", "aborted", "error"):
                return

        if entries:
            continue

        async with async_session_factory() as db:
            run = await AgentService(db).get_run(user_id, run_id)
            if run.status in TERMINAL_RUN_STATUSES:
                event = {"completed": "done", "canceled": "aborted"}.get(run.status, "error")
                yield _sse(
                    event,
                    {
                        "run_id": str(run.id),
                        "status": run.status,
                        "message": run.error_message,
                    },
                    run.last_event_id,
                )
                return


def _sse(event: str, data: dict, event_id: str | None = None) -> dict[str, str]:
    """把业务事件转换为 sse-starlette 接受的事件字典。"""
    payload = {"event": event, "data": json.dumps(data, ensure_ascii=False)}
    if event_id:
        payload["id"] = event_id
    return payload
