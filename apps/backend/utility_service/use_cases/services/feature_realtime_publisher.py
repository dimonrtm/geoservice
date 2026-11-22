from __future__ import annotations

from collections.abc import Callable
from uuid import UUID, uuid4

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut

PublishFeatureChange = Callable[[RealtimeEventContext, FeatureOut | None], None]


class FeatureRealtimePublisher:
    def __init__(self, publish_change: PublishFeatureChange) -> None:
        self._publish_change = publish_change

    async def publish_feature_created(
        self, layer_id: UUID, feature: FeatureOut, *, context: RealtimeEventContext | None = None
    ) -> None:
        context = context or RealtimeEventContext(
            self._generate_event_id(), "feature_created", layer_id, feature.id, feature.version
        )
        self._publish_change(context, feature)

    async def publish_feature_updated(
        self, layer_id: UUID, feature: FeatureOut, *, context: RealtimeEventContext | None = None
    ) -> None:
        context = context or RealtimeEventContext(
            self._generate_event_id(), "feature_updated", layer_id, feature.id, feature.version
        )
        self._publish_change(context, feature)

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
        self._publish_change(context, None)

    def _generate_event_id(self) -> str:
        return f"evt_{uuid4()}"
