from datetime import datetime, timezone

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.web_api.realtime.realtime_connection_manager import WebSocketConnectionManager


def build_feature_event(
    context: RealtimeEventContext, feature: FeatureOut | None
) -> dict[str, object]:
    event: dict[str, object] = {
        "type": context.event_type,
        "eventId": context.event_id,
        "occurredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "layerId": str(context.layer_id),
    }
    if feature is None:
        event.update(featureId=str(context.feature_id), deletedVersion=context.feature_version)
    else:
        event["feature"] = feature.model_dump(mode="json")
    return event


def publish_feature_change(
    manager: WebSocketConnectionManager, context: RealtimeEventContext, feature: FeatureOut | None
) -> None:
    manager.publish_event(context, lambda: build_feature_event(context, feature))
