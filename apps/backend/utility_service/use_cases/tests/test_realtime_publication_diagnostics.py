import asyncio
import json
from uuid import uuid4

import pytest

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_feature_realtime_publisher import build_feature
from utility_service.use_cases.tests.test_realtime_connection_manager import (
    DummyWebSocket,
    active_session,
    build_user_context,
)


def diagnostic_records(caplog):
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "utility_service.realtime"
    ]


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


def test_event_id_matches_wire_payload():
    async def scenario():
        layer, socket = uuid4(), DummyWebSocket()
        manager = WebSocketConnectionManager(active_session)
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        feature = build_feature()
        context = RealtimeEventContext("evt_shared", "feature_updated", layer, feature.id, 2)
        await FeatureRealtimePublisher(manager).publish_feature_updated(
            layer, feature, context=context
        )
        payload = await socket.next_event()
        assert payload["eventId"] == "evt_shared"
        assert payload["feature"] == feature.model_dump(mode="json")
        await manager.shutdown()

    asyncio.run(scenario())


def test_feature_service_logs_unknown_recipients_on_publisher_failure(caplog):
    class FailingPublisher:
        async def publish_feature_updated(self, *args, **kwargs):
            raise RuntimeError("SECRET")

    feature, layer = build_feature(), uuid4()
    service = FeatureService(None, None, FailingPublisher())
    asyncio.run(service.publish_feature_updated(layer, feature))
    records = diagnostic_records(caplog)
    assert len(records) == 1
    assert records[0]["event"] == "realtime_publication_failed"
    assert records[0]["featureId"] == str(feature.id)
    assert records[0]["featureVersion"] == 2
    assert records[0]["eventType"] == "feature_updated"
    assert records[0]["eventId"].startswith("evt_")
    assert "connectionId" not in records[0]


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
