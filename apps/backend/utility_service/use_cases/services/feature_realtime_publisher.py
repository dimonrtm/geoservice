from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)


class FeatureRealtimePublisher:
    def __init__(self, connection_manager: WebSocketConnectionManager):
        self.connection_manager = connection_manager

    async def publish_feature_created(self, layer_id: UUID, feature: FeatureOut) -> None:
        await self.connection_manager.broadcast_to_layer(
            layer_id,
            {
                "type": "feature_created",
                "eventId": self._generate_event_id(),
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "feature": feature.model_dump(mode="json"),
            },
        )

    async def publish_feature_updated(self, layer_id: UUID, feature: FeatureOut) -> None:
        await self.connection_manager.broadcast_to_layer(
            layer_id,
            {
                "type": "feature_updated",
                "eventId": self._generate_event_id(),
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "feature": feature.model_dump(mode="json"),
            },
        )

    async def publish_feature_deleted(self, layer_id: UUID, feature_id: UUID) -> None:
        await self.connection_manager.broadcast_to_layer(
            layer_id,
            {
                "type": "feature_deleted",
                "eventId": self._generate_event_id(),
                "occurredAt": self._generate_occurred_at(),
                "layerId": str(layer_id),
                "featureId": str(feature_id),
            },
        )

    def _generate_event_id(self) -> str:
        return f"evt_{uuid4()}"

    def _generate_occurred_at(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
