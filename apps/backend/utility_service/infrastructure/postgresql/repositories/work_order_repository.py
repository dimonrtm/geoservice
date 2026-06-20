from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
)


class WorkOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, work_order_id: UUID) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        return result.scalars().one_or_none()

    async def get_by_code(self, code: str) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.code == code))
        return result.scalars().one_or_none()

    async def list_assigned_to_user(self, user_id: UUID) -> list[WorkOrder]:
        result = await self.session.execute(
            select(WorkOrder)
            .where(WorkOrder.assignee_user_id == user_id)
            .order_by(WorkOrder.created_at, WorkOrder.code)
        )
        return list(result.scalars().all())

    async def save(self, work_order: WorkOrder) -> None:
        self.session.add(work_order)
        await self.session.flush()

    async def get_open_edit_version(self, work_order_id: UUID) -> EditVersion | None:
        result = await self.session.execute(
            select(EditVersion).where(
                EditVersion.work_order_id == work_order_id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        return result.scalars().one_or_none()

    async def create_open_edit_version(
        self,
        *,
        work_order_id: UUID,
        default_state_id: UUID,
        base_network_revision: int,
        default_features: Sequence[Any],
        default_associations: Sequence[Any],
        owner_user_id: UUID,
    ) -> EditVersion:
        edit_version = EditVersion(
            work_order_id=work_order_id,
            default_state_id=default_state_id,
            owner_user_id=owner_user_id,
            base_network_revision=base_network_revision,
            status=EditVersionStatus.OPEN,
        )
        self.session.add(edit_version)
        await self.session.flush()

        self.session.add_all(
            [
                EditVersionFeature(
                    edit_version_id=edit_version.id,
                    feature_id=feature.feature_id,
                    asset_code=feature.asset_code,
                    feature_type=feature.feature_type,
                    geometry=feature.geometry,
                    properties=dict(feature.properties),
                    network_version=feature.network_version,
                )
                for feature in default_features
            ]
        )
        # Associations have composite FKs to edit_version_features; insert parents first.
        await self.session.flush()

        self.session.add_all(
            [
                EditVersionAssociation(
                    edit_version_id=edit_version.id,
                    association_id=association.association_id,
                    association_type=association.association_type,
                    from_feature_id=association.from_feature_id,
                    to_feature_id=association.to_feature_id,
                    properties=dict(association.properties),
                    network_version=association.network_version,
                )
                for association in default_associations
            ]
        )
        await self.session.flush()
        return edit_version

    async def touch_edit_version(self, edit_version: EditVersion) -> None:
        edit_version.last_opened_at = datetime.now(timezone.utc)
        self.session.add(edit_version)
        await self.session.flush()
