"""Test-only ORM transaction; deliberately not a Save service."""

import json
from datetime import datetime, timezone
from uuid import UUID

from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionCommand,
    EditVersionCommandState,
    EditVersionChangeEvent,
    EditVersionChangeEventType,
    EditVersionFeature,
)
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)


async def persist_orm_change(
    session: AsyncSession,
    context: dict[str, UUID],
    command_id: UUID,
    *,
    before_geometry: str,
    after_geometry: str,
) -> None:
    version = (
        await session.scalars(
            select(EditVersion)
            .where(EditVersion.id == context["edit_version_id"])
            .with_for_update()
        )
    ).one()
    before_revision = version.draft_revision
    command = EditVersionCommand(
        command_id=command_id,
        edit_version_id=version.id,
        feature_id=context["feature_id"],
        actor_user_id=context["actor_user_id"],
        request_fingerprint="orm-fixture",
        state=EditVersionCommandState.RUNNING,
        response_payload=None,
    )
    session.add(command)
    await session.flush()
    feature = (
        await session.scalars(
            select(EditVersionFeature)
            .where(
                EditVersionFeature.edit_version_id == version.id,
                EditVersionFeature.feature_id == context["feature_id"],
            )
            .with_for_update()
        )
    ).one()
    feature.geometry = WKTElement(
        after_geometry,
        srid=4326,
    )
    feature.operation = EditVersionOperationState.UPDATED
    version.draft_revision += 1
    geometry = json.loads(
        await session.scalar(
            select(
                func.ST_AsGeoJSON(
                    WKTElement(
                        after_geometry,
                        srid=4326,
                    )
                )
            )
        )
    )
    command.state = EditVersionCommandState.SUCCEEDED
    command.response_status = 200
    command.response_payload = {
        "commandId": str(command_id),
        "commandState": "succeeded",
        "draftVersionToken": str(version.draft_revision),
        "operation": "updated",
        "hasPersistedChangeSet": True,
        "updatedFeature": {
            "id": str(feature.feature_id),
            "geometry": geometry,
        },
        "basicValidation": {
            "geometryStatus": "passed",
            "aoiStatus": "passed",
            "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
            "dirtyRelativeToBaseline": "passed",
        },
    }
    command.completed_at = datetime.now(timezone.utc)
    await session.flush()
    session.add(
        EditVersionChangeEvent(
            command_id=command_id,
            edit_version_id=version.id,
            work_order_id=version.work_order_id,
            default_state_id=version.default_state_id,
            feature_id=feature.feature_id,
            actor_user_id=context["actor_user_id"],
            event_type=EditVersionChangeEventType.CHANGE_SET_PERSISTED,
            before_geometry=WKTElement(
                before_geometry,
                srid=4326,
            ),
            after_geometry=WKTElement(
                after_geometry,
                srid=4326,
            ),
            base_network_revision=version.base_network_revision,
            draft_revision_before=before_revision,
            draft_revision_after=version.draft_revision,
        )
    )
    await session.flush()
