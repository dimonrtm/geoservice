import asyncio
from datetime import datetime
from uuid import uuid4

from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.services.feature_realtime_publisher import (
    FeatureRealtimePublisher,
)
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import (
    DummyWebSocket,
    active_session,
    build_user_context,
)


POLYGON_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 10.0)]],
}


def build_feature() -> FeatureOut:
    return FeatureOut(
        id=uuid4(),
        version=2,
        properties={"name": "Feature"},
        geometry=POLYGON_GEOMETRY,
    )


def assert_common_event_fields(payload: dict[str, object], layer_id) -> None:
    assert payload["layerId"] == str(layer_id)
    assert isinstance(payload["eventId"], str)
    assert str(payload["eventId"]).startswith("evt_")
    assert isinstance(payload["occurredAt"], str)
    assert str(payload["occurredAt"]).endswith("Z")
    datetime.fromisoformat(str(payload["occurredAt"]).replace("Z", "+00:00"))


async def capture_publication(layer_id, operation):
    manager = WebSocketConnectionManager(active_session)
    socket = DummyWebSocket()
    await manager.connect(layer_id, socket, build_user_context())
    await socket.next_event()
    try:
        await operation(FeatureRealtimePublisher(manager))
        return await socket.next_event()
    finally:
        await manager.shutdown()


def test_publish_feature_created_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature = build_feature()
    payload = asyncio.run(
        capture_publication(
            layer_id, lambda publisher: publisher.publish_feature_created(layer_id, feature)
        )
    )
    assert payload["type"] == "feature_created"
    assert payload["feature"] == feature.model_dump(mode="json")
    assert_common_event_fields(payload, layer_id)


def test_publish_feature_updated_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature = build_feature()
    payload = asyncio.run(
        capture_publication(
            layer_id, lambda publisher: publisher.publish_feature_updated(layer_id, feature)
        )
    )
    assert payload["type"] == "feature_updated"
    assert payload["feature"] == feature.model_dump(mode="json")
    assert_common_event_fields(payload, layer_id)


def test_publish_feature_deleted_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature_id = uuid4()
    payload = asyncio.run(
        capture_publication(
            layer_id, lambda publisher: publisher.publish_feature_deleted(layer_id, feature_id, 3)
        )
    )
    assert payload["type"] == "feature_deleted"
    assert payload["deletedVersion"] == 3
    assert payload["featureId"] == str(feature_id)
    assert_common_event_fields(payload, layer_id)
