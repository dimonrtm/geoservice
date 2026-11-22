import asyncio
from uuid import uuid4

import pytest

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.web_api.realtime.realtime_connection_manager import WebSocketConnectionManager
from utility_service.use_cases.tests.test_realtime_publication_diagnostics import diagnostic_records
from utility_service.web_api.tests.realtime_support import (
    DummyWebSocket,
    active_session,
    build_user_context,
)


@pytest.mark.parametrize("stage", ["prepare", "serialize"])
def test_publication_failure_logs_each_target(caplog, stage):
    async def scenario():
        layer = uuid4()
        manager = WebSocketConnectionManager(active_session)
        sockets = [DummyWebSocket(), DummyWebSocket()]
        for socket in sockets:
            await manager.connect(layer, socket, build_user_context())
            await socket.next_event()
        context = RealtimeEventContext("evt_failed", "feature_updated", layer, uuid4(), 3)

        def build():
            if stage == "prepare":
                raise ValueError("SECRET")
            return {"invalid": float("nan")}

        manager.publish_event(context, build)
        records = diagnostic_records(caplog)
        assert len(records) == 2
        assert len({item["connectionId"] for item in records}) == 2
        assert {item["eventId"] for item in records} == {"evt_failed"}
        assert {item["reason"] for item in records} == {"publication_failed"}
        assert {item["stage"] for item in records} == {stage}
        assert {item["featureVersion"] for item in records} == {3}
        assert "SECRET" not in caplog.text
        await manager.shutdown()

    asyncio.run(scenario())


def test_empty_snapshot_skips_build_and_logging(caplog):
    manager = WebSocketConnectionManager(active_session)
    context = RealtimeEventContext("evt_empty", "feature_created", uuid4(), uuid4(), 1)

    def build():
        pytest.fail("No recipients: payload must not be constructed")

    manager.publish_event(context, build)
    assert diagnostic_records(caplog) == []


def test_partial_fanout_reports_only_remaining_targets(caplog, monkeypatch):
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        layer = uuid4()
        sockets = [DummyWebSocket(), DummyWebSocket(), DummyWebSocket()]
        for socket in sockets:
            await manager.connect(layer, socket, build_user_context())
            await socket.next_event()
        second = manager._connections[layer][sockets[1]]

        def fail_put(frame):
            raise RuntimeError("queue infrastructure failed")

        monkeypatch.setattr(second.queue, "put_nowait", fail_put)
        context = RealtimeEventContext("evt_partial", "feature_updated", layer, uuid4(), 3)
        manager.publish_event(
            context, lambda: {"type": "feature_updated", "eventId": "evt_partial"}
        )
        assert (await sockets[0].next_event())["eventId"] == "evt_partial"
        records = diagnostic_records(caplog)
        assert len(records) == 2
        assert str(manager._connections[layer][sockets[0]].connection_id) not in {
            item["connectionId"] for item in records
        }
        await manager.shutdown()

    asyncio.run(scenario())
