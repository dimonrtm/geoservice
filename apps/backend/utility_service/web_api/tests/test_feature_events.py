import asyncio
from datetime import datetime
from uuid import uuid4

import pytest

from utility_service.realtime_dependencies import get_feature_realtime_publisher
from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.use_cases.tests.test_feature_realtime_publisher import build_feature
from utility_service.use_cases.tests.test_realtime_publication_diagnostics import diagnostic_records
from utility_service.web_api.realtime import feature_events
from utility_service.web_api.realtime.realtime_connection_manager import WebSocketConnectionManager
from utility_service.web_api.tests.realtime_support import (
    DummyWebSocket,
    active_session,
    build_user_context,
)


@pytest.mark.parametrize("event_type", ["feature_created", "feature_updated", "feature_deleted"])
def test_feature_event_wire_format(event_type):
    layer, feature = uuid4(), build_feature()
    context = RealtimeEventContext("evt_shared", event_type, layer, feature.id, feature.version)
    snapshot = None if event_type == "feature_deleted" else feature
    event = feature_events.build_feature_event(context, snapshot)
    timestamp = event.pop("occurredAt")
    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    expected = {"type": event_type, "eventId": "evt_shared", "layerId": str(layer)}
    if snapshot is None:
        expected.update(featureId=str(feature.id), deletedVersion=feature.version)
    else:
        expected["feature"] = feature.model_dump(mode="json")
    assert event == expected


@pytest.mark.parametrize(
    ("recipients", "fail_build", "provided_id"),
    [(0, False, None), (2, False, "evt_shared"), (2, False, None), (2, True, "evt_shared")],
)
def test_prepares_one_message_only_for_subscribers(
    recipients, fail_build, provided_id, monkeypatch, caplog
):
    manager = WebSocketConnectionManager(active_session)
    publisher = get_feature_realtime_publisher(manager)
    layer, feature = uuid4(), build_feature()
    context = (
        RealtimeEventContext(provided_id, "feature_updated", layer, feature.id, feature.version)
        if provided_id
        else None
    )
    original = feature_events.build_feature_event
    builds = []

    def record_build(ctx, snapshot):
        builds.append(ctx.event_id)
        if fail_build:
            raise ValueError("cannot prepare")
        return original(ctx, snapshot)

    monkeypatch.setattr(feature_events, "build_feature_event", record_build)

    async def scenario():
        sockets = [DummyWebSocket() for _ in range(recipients)]
        try:
            for socket in sockets:
                await manager.connect(layer, socket, build_user_context())
                await socket.next_event()
            await publisher.publish_feature_updated(layer, feature, context=context)
            records = diagnostic_records(caplog)
            if not recipients:
                assert builds == [] and records == []
                return
            [event_id] = builds
            assert event_id.startswith("evt_")
            if provided_id:
                assert event_id == provided_id
            if fail_build:
                assert len(records) == 2
                assert len({item["connectionId"] for item in records}) == 2
                assert {(item["eventId"], item["stage"]) for item in records} == {
                    (event_id, "prepare")
                }
            else:
                assert records == []
                for socket in sockets:
                    event = await socket.next_event()
                    assert event["eventId"] == event_id
                    assert event["feature"] == feature.model_dump(mode="json")
        finally:
            await manager.shutdown()

    asyncio.run(scenario())
