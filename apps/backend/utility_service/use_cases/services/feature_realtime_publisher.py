from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext

from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)


class FeatureRealtimePublisher:
    def __init__(self, connection_manager: WebSocketConnectionManager):
        self.connection_manager = connection_manager

    async def publish_feature_created(
        self, layer_id: UUID, feature: FeatureOut, *, context: RealtimeEventContext | None = None
    ) -> None:
        context = context or RealtimeEventContext(
            self._generate_event_id(), "feature_created", layer_id, feature.id, feature.version
        )
        self.connection_manager.publish_event(
            context,
            lambda: {
                "type": "feature_created",
                "eventId": context.event_id,
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "feature": feature.model_dump(mode="json"),
            },
        )

    async def publish_feature_updated(
        self, layer_id: UUID, feature: FeatureOut, *, context: RealtimeEventContext | None = None
    ) -> None:
        context = context or RealtimeEventContext(
            self._generate_event_id(), "feature_updated", layer_id, feature.id, feature.version
        )
        self.connection_manager.publish_event(
            context,
            lambda: {
                "type": "feature_updated",
                "eventId": context.event_id,
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "feature": feature.model_dump(mode="json"),
            },
        )

    async def publish_feature_deleted(
        self,
        layer_id: UUID,
        feature_id: UUID,
        deleted_version: int,
        *,
        context: RealtimeEventContext | None = None,
    ) -> None:
        context = context or RealtimeEventContext(
            self._generate_event_id(), "feature_deleted", layer_id, feature_id, deleted_version
        )
        self.connection_manager.publish_event(
            context,
            lambda: {
                "type": "feature_deleted",
                "eventId": context.event_id,
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "featureId": str(feature_id),
                "deletedVersion": deleted_version,
            },
        )

    def _generate_event_id(self) -> str:
        return f"evt_{uuid4()}"

    def _generate_occurred_at(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
