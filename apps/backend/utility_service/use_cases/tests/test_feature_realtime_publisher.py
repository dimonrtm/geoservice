import asyncio
from uuid import uuid4

import pytest

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
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


@pytest.mark.parametrize("event_type", ["feature_created", "feature_updated", "feature_deleted"])
@pytest.mark.parametrize("supply_context", [False, True])
def test_publishes_committed_change(event_type, supply_context):
    feature = build_feature()
    layer = uuid4()
    context = (
        RealtimeEventContext("evt_known", event_type, layer, feature.id, feature.version)
        if supply_context
        else None
    )
    changes = []
    publisher = FeatureRealtimePublisher(lambda ctx, snapshot: changes.append((ctx, snapshot)))
    if event_type == "feature_created":
        operation = publisher.publish_feature_created(layer, feature, context=context)
    elif event_type == "feature_updated":
        operation = publisher.publish_feature_updated(layer, feature, context=context)
    else:
        operation = publisher.publish_feature_deleted(
            layer, feature.id, feature.version, context=context
        )
    asyncio.run(operation)
    [(published, snapshot)] = changes
    assert published.event_id.startswith("evt_")
    assert published == RealtimeEventContext(
        published.event_id, event_type, layer, feature.id, feature.version
    )
    if supply_context:
        assert published is context
    assert snapshot is (None if event_type == "feature_deleted" else feature)
