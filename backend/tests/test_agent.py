import unittest
from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.schemas.agent import AgentRunResponse, AgentRunSubmit, AgentThreadResponse
from app.services.agent.agent_service import AgentService
from app.services.agent.event_stream import AgentEventStream
from app.services.agent.graph import build_general_chat_graph
from app.services.agent.runtime_model_config_service import RuntimeModelConfigService


class FakeRedis:
    def __init__(self) -> None:
        self.entries = defaultdict(list)
        self.sequence = 0

    async def xadd(self, key, fields, **kwargs):
        self.sequence += 1
        event_id = f"{self.sequence}-0"
        self.entries[key].append((event_id, fields))
        return event_id

    async def expire(self, key, ttl):
        return True

    async def xread(self, streams, **kwargs):
        key, cursor = next(iter(streams.items()))
        cursor_sequence = int(cursor.split("-", 1)[0])
        rows = [row for row in self.entries[key] if int(row[0].split("-", 1)[0]) > cursor_sequence]
        return [(key, rows)] if rows else []


class AgentTests(unittest.IsolatedAsyncioTestCase):
    def test_available_model_option_excludes_api_key(self) -> None:
        config = SimpleNamespace(
            id=4,
            name="通义千问",
            provider="openai_compatible",
            base_url="https://example.com/v1",
            model="qwen-plus",
            api_key_ciphertext="encrypted-secret",
            max_output_tokens=4096,
            temperature=0.7,
        )

        option = RuntimeModelConfigService._to_model_option(config)

        self.assertEqual(option.model_config_id, 4)
        self.assertEqual(option.model_name, "qwen-plus")
        self.assertTrue(option.api_key_configured)
        self.assertNotIn("api_key_ciphertext", option.model_dump())

    async def test_delete_thread_soft_deletes_without_active_run(self) -> None:
        service = AgentService(AsyncMock())
        thread = SimpleNamespace(status="active", deleted_at=None)
        service.get_thread = AsyncMock(return_value=thread)
        service.get_active_run = AsyncMock(return_value=None)

        active_run = await service.delete_thread(1, uuid4())

        self.assertIsNone(active_run)
        self.assertEqual(thread.status, "deleted")
        self.assertIsNotNone(thread.deleted_at)
        service.db.flush.assert_awaited_once()

    async def test_delete_thread_cancels_pending_run(self) -> None:
        service = AgentService(AsyncMock())
        thread = SimpleNamespace(status="active", deleted_at=None)
        run = SimpleNamespace(status="pending", finish_reason=None, finished_at=None)
        service.get_thread = AsyncMock(return_value=thread)
        service.get_active_run = AsyncMock(return_value=run)
        service._update_assistant = AsyncMock()

        active_run = await service.delete_thread(1, uuid4())

        self.assertIs(active_run, run)
        self.assertEqual(run.status, "canceled")
        self.assertEqual(run.finish_reason, "abort")
        self.assertIsNotNone(run.finished_at)
        service._update_assistant.assert_awaited_once_with(run, status="canceled", finish_reason="abort")

    async def test_delete_thread_requests_abort_for_running_run(self) -> None:
        service = AgentService(AsyncMock())
        thread = SimpleNamespace(status="active", deleted_at=None)
        run = SimpleNamespace(status="running")
        service.get_thread = AsyncMock(return_value=thread)
        service.get_active_run = AsyncMock(return_value=run)

        active_run = await service.delete_thread(1, uuid4())

        self.assertIs(active_run, run)
        self.assertEqual(run.status, "cancel_requested")
        self.assertEqual(thread.status, "deleted")

    async def test_general_graph_streams_model_tokens(self) -> None:
        graph = build_general_chat_graph(
            llm=FakeListChatModel(responses=["hello"]),
            system_prompt="test",
            checkpointer=InMemorySaver(),
        )
        chunks = []
        async for chunk, _metadata in graph.astream(
            {"messages": [HumanMessage(content="hi")]},
            config={"configurable": {"thread_id": "test-thread"}},
            stream_mode="messages",
        ):
            chunks.append(chunk.content)

        self.assertEqual(chunks, ["h", "e", "l", "l", "o"])

    async def test_event_stream_replays_after_cursor(self) -> None:
        stream = AgentEventStream(FakeRedis())
        run_id = uuid4()
        first_id = await stream.publish(run_id, "delta", {"content": "a"})
        await stream.publish(run_id, "delta", {"content": "b"})

        events = await stream.read(run_id, first_id, block_ms=1)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], "delta")
        self.assertEqual(events[0][2], {"content": "b"})

    async def test_submit_run_creates_thread_when_omitted(self) -> None:
        service = AgentService(AsyncMock())
        thread_id = uuid4()
        response = AgentRunResponse(
            run_id=uuid4(),
            thread_id=thread_id,
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            status="pending",
        )
        service._get_by_client_request = AsyncMock(return_value=None)
        service.create_thread = AsyncMock(
            return_value=AgentThreadResponse(
                thread_id=thread_id,
                title="New conversation",
                capability="general",
                model_config_id=4,
                status="active",
                message_count=0,
                created_at=datetime.now(),
            )
        )
        service.create_run = AsyncMock(return_value=response)

        result = await service.submit_run(
            1,
            AgentRunSubmit(message="hello", model_config_id=4, client_request_id="request-1"),
        )

        self.assertIs(result, response)
        service.create_thread.assert_awaited_once()
        self.assertEqual(service.create_run.await_args.args[1], thread_id)

    async def test_submit_run_reuses_idempotent_run(self) -> None:
        service = AgentService(AsyncMock())
        existing = SimpleNamespace(
            id=uuid4(),
            thread_id=uuid4(),
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            status="running",
            content_snapshot="partial",
            last_event_id="1-0",
            model_name="test-model",
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            error_message=None,
            created_at=datetime.now(),
            started_at=datetime.now(),
            finished_at=None,
        )
        service._get_by_client_request = AsyncMock(return_value=existing)
        service.create_thread = AsyncMock()
        service.create_run = AsyncMock()

        result = await service.submit_run(
            1,
            AgentRunSubmit(message="hello", model_config_id=4, client_request_id="request-1"),
        )

        self.assertEqual(result.run_id, existing.id)
        service.create_thread.assert_not_awaited()
        service.create_run.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
