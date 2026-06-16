import asyncio
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher


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


def test_publish_feature_created_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature = build_feature()
    connection_manager = AsyncMock()
    publisher = FeatureRealtimePublisher(connection_manager)

    asyncio.run(publisher.publish_feature_created(layer_id, feature))

    connection_manager.broadcast_to_layer.assert_awaited_once()
    call_args = connection_manager.broadcast_to_layer.await_args.args
    assert call_args[0] == layer_id
    payload = call_args[1]
    assert payload["type"] == "feature_created"
    assert payload["feature"] == feature.model_dump(mode="json")
    assert_common_event_fields(payload, layer_id)


def test_publish_feature_updated_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature = build_feature()
    connection_manager = AsyncMock()
    publisher = FeatureRealtimePublisher(connection_manager)

    asyncio.run(publisher.publish_feature_updated(layer_id, feature))

    payload = connection_manager.broadcast_to_layer.await_args.args[1]
    assert payload["type"] == "feature_updated"
    assert payload["feature"] == feature.model_dump(mode="json")
    assert_common_event_fields(payload, layer_id)


def test_publish_feature_deleted_sends_expected_payload() -> None:
    layer_id = uuid4()
    feature_id = uuid4()
    connection_manager = AsyncMock()
    publisher = FeatureRealtimePublisher(connection_manager)

    asyncio.run(publisher.publish_feature_deleted(layer_id, feature_id))

    payload = connection_manager.broadcast_to_layer.await_args.args[1]
    assert payload["type"] == "feature_deleted"
    assert payload["featureId"] == str(feature_id)
    assert_common_event_fields(payload, layer_id)
