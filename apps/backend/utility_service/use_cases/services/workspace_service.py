from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.workspace import (
    WorkspaceAssociationOut,
    WorkspaceAoiOut,
    WorkspaceEditVersionOut,
    WorkspaceFeatureCollectionOut,
    WorkspaceFeatureOut,
    WorkspaceOut,
    WorkspaceScopeOut,
    WorkspaceWorkOrderOut,
)


class WorkspaceService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository

    async def get_workspace(
        self,
        work_order_id: UUID,
        edit_version_id: UUID,
        actor_id: UUID,
    ) -> WorkspaceOut:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None or actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

        aggregate = await self.work_order_repository.get_workspace_aggregate(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
        if aggregate is None or aggregate.work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(
                404,
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия не найдена.",
            )

        if (
            aggregate.work_order.status is not WorkOrderStatus.IN_PROGRESS
            or aggregate.edit_version.status is not EditVersionStatus.OPEN
        ):
            raise WorkOrderApiError(
                409,
                "EDIT_VERSION_STATE_CONFLICT",
                "Состояние рабочей версии не допускает операцию.",
            )

        try:
            return self.workspace_from_aggregate(aggregate)
        except (AttributeError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise WorkOrderApiError(
                422,
                "WORKSPACE_CONTEXT_INVALID",
                "Workspace невозможно сформировать из текущих данных.",
            ) from exc

    def workspace_from_aggregate(
        self,
        aggregate: WorkspaceAggregateRow,
    ) -> WorkspaceOut:
        if aggregate.aoi is None:
            raise ValueError("missing AOI")

        aoi = WorkspaceAoiOut(
            id=aggregate.aoi.id,
            name=aggregate.aoi.name,
            description=aggregate.aoi.description,
            geometry=aggregate.aoi.geometry_data,
            extent=list(aggregate.aoi.extent),
        )
        features = [
            WorkspaceFeatureOut(
                id=feature["id"],
                geometry=feature["geometry_data"],
                properties=self.feature_properties(feature),
            )
            for feature in aggregate.features_data
        ]
        return WorkspaceOut(
            work_order=WorkspaceWorkOrderOut(
                id=aggregate.work_order.id,
                code=aggregate.work_order.code,
                title=aggregate.work_order.title,
                description=aggregate.work_order.description,
                status=aggregate.work_order.status.value,
                scope=WorkspaceScopeOut(aoi=aoi),
                edit_version=WorkspaceEditVersionOut(
                    id=aggregate.edit_version.id,
                    status=aggregate.edit_version.status.value,
                    base_network_revision=aggregate.edit_version.base_network_revision,
                    features=WorkspaceFeatureCollectionOut(features=features),
                    associations=[
                        WorkspaceAssociationOut(
                            **{
                                **association,
                                "association_type": self.association_type_value(
                                    association["association_type"]
                                ),
                            }
                        )
                        for association in aggregate.associations_data
                    ],
                ),
            )
        )

    def feature_properties(self, feature: dict[str, Any]) -> dict[str, Any]:
        return {
            **dict(feature["properties"]),
            "assetCode": feature["asset_code"],
            "featureType": feature["feature_type"],
            "networkVersion": feature["network_version"],
            "operation": feature["operation"],
        }

    def association_type_value(self, association_type: Any) -> str:
        value = getattr(association_type, "value", association_type)
        return str(value)
