from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import cast, func, literal, select
from sqlalchemy.dialects.postgresql import JSONB, aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    AOI,
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
)


@dataclass(frozen=True)
class WorkspaceAoiRow:
    id: UUID
    name: str
    description: str | None
    geometry_data: dict[str, Any]
    extent: list[float]


@dataclass(frozen=True)
class WorkspaceAggregateRow:
    work_order: WorkOrder
    edit_version: EditVersion
    aoi: WorkspaceAoiRow
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]


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
            .order_by(WorkOrder.updated_at.desc(), WorkOrder.code.asc())
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

    async def get_workspace_aggregate(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
    ) -> WorkspaceAggregateRow | None:
        empty_array = cast(literal("[]"), JSONB)

        workspace_feature_ids = (
            select(EditVersionFeature.feature_id)
            .where(
                EditVersionFeature.edit_version_id == EditVersion.id,
                func.ST_Intersects(AOI.geometry, EditVersionFeature.geometry),
            )
            .correlate(EditVersion, AOI)
        )

        feature_json = func.jsonb_build_object(
            "id",
            EditVersionFeature.feature_id,
            "asset_code",
            EditVersionFeature.asset_code,
            "feature_type",
            EditVersionFeature.feature_type,
            "geometry_data",
            cast(func.ST_AsGeoJSON(EditVersionFeature.geometry), JSONB),
            "properties",
            EditVersionFeature.properties,
            "network_version",
            EditVersionFeature.network_version,
            "operation",
            EditVersionFeature.operation,
        )
        features_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            feature_json,
                            EditVersionFeature.asset_code,
                            EditVersionFeature.feature_id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(
                EditVersionFeature.edit_version_id == EditVersion.id,
                EditVersionFeature.feature_id.in_(workspace_feature_ids),
            )
            .correlate(EditVersion, AOI)
            .scalar_subquery()
        )

        association_json = func.jsonb_build_object(
            "id",
            EditVersionAssociation.association_id,
            "from_feature_id",
            EditVersionAssociation.from_feature_id,
            "to_feature_id",
            EditVersionAssociation.to_feature_id,
            "association_type",
            EditVersionAssociation.association_type,
            "version",
            EditVersionAssociation.network_version,
        )
        associations_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            association_json,
                            EditVersionAssociation.from_feature_id,
                            EditVersionAssociation.to_feature_id,
                            EditVersionAssociation.association_type,
                            EditVersionAssociation.association_id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(
                EditVersionAssociation.edit_version_id == EditVersion.id,
                EditVersionAssociation.from_feature_id.in_(workspace_feature_ids),
                EditVersionAssociation.to_feature_id.in_(workspace_feature_ids),
            )
            .correlate(EditVersion, AOI)
            .scalar_subquery()
        )

        extent_data = func.jsonb_build_array(
            func.ST_XMin(func.Box2D(AOI.geometry)),
            func.ST_YMin(func.Box2D(AOI.geometry)),
            func.ST_XMax(func.Box2D(AOI.geometry)),
            func.ST_YMax(func.Box2D(AOI.geometry)),
        )

        result = await self.session.execute(
            select(
                WorkOrder,
                EditVersion,
                AOI.id.label("aoi_id"),
                AOI.name.label("aoi_name"),
                AOI.description.label("aoi_description"),
                cast(func.ST_AsGeoJSON(AOI.geometry), JSONB).label("aoi_geometry_data"),
                extent_data.label("aoi_extent"),
                features_data.label("features_data"),
                associations_data.label("associations_data"),
            )
            .join(EditVersion, EditVersion.work_order_id == WorkOrder.id)
            .join(AOI, WorkOrder.aoi_id == AOI.id)
            .where(
                WorkOrder.id == work_order_id,
                EditVersion.id == edit_version_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        return WorkspaceAggregateRow(
            work_order=row.WorkOrder,
            edit_version=row.EditVersion,
            aoi=WorkspaceAoiRow(
                id=row.aoi_id,
                name=row.aoi_name,
                description=row.aoi_description,
                geometry_data=row.aoi_geometry_data,
                extent=row.aoi_extent,
            ),
            features_data=row.features_data,
            associations_data=row.associations_data,
        )
