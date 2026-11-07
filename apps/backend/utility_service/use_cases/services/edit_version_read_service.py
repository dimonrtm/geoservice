from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    geometry_to_geojson,
)
from utility_service.use_cases.services.version_change_projection import (
    project_version_changes,
    validate_baseline,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.use_cases.schemas.edit_version.change_set import VersionChangeSetOut
from utility_service.use_cases.schemas.edit_version.feature_baseline import FeatureBaselineOut

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_read import (
    EditVersionMapRow,
    VersionComparisonRow,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.edit_version.version_map import (
    MapAssociationOut,
    MapAoiOut,
    MapEditVersionOut,
    MapFeatureCollectionOut,
    MapFeatureOut,
    EditVersionMapOut,
    MapScopeOut,
    MapWorkOrderOut,
)


class EditVersionReadService:
    def __init__(
        self,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        default_state_repository: DefaultStateRepository,
    ):
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.default_state_repository = default_state_repository

    async def require_editor(self, actor_id: UUID) -> None:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None or actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    @staticmethod
    def require_version_access(
        actor_id: UUID,
        assignee_id: UUID,
        work_order_status: WorkOrderStatus,
        version_status: EditVersionStatus,
    ) -> None:
        if assignee_id != actor_id:
            raise WorkOrderApiError(
                404,
                "EDIT_VERSION_NOT_FOUND",
                "Рабочая версия не найдена.",
            )

        if (
            work_order_status is not WorkOrderStatus.IN_PROGRESS
            or version_status is not EditVersionStatus.OPEN
        ):
            raise WorkOrderApiError(
                409,
                "EDIT_VERSION_STATE_CONFLICT",
                "Состояние рабочей версии не допускает операцию.",
            )

    async def get_version_map(
        self, work_order_id: UUID, edit_version_id: UUID, actor_id: UUID
    ) -> EditVersionMapOut:
        await self.require_editor(actor_id)
        version_map = await self.work_order_repository.get_edit_version_map(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
        if version_map is None:
            raise WorkOrderApiError(404, "EDIT_VERSION_NOT_FOUND", "Рабочая версия не найдена.")
        self.require_version_access(
            actor_id,
            version_map.work_order.assignee_user_id,
            version_map.work_order.status,
            version_map.edit_version.status,
        )
        with valid_readback():
            return self.map_response(version_map)

    async def read_comparison(
        self,
        work_order_id: UUID,
        edit_version_id: UUID,
        actor_id: UUID,
        feature_id: UUID | None = None,
    ) -> VersionComparisonRow:
        await self.require_editor(actor_id)
        version = await self.work_order_repository.read_version_comparison(
            work_order_id, edit_version_id, feature_id
        )
        if version is None:
            raise WorkOrderApiError(404, "EDIT_VERSION_NOT_FOUND", "Рабочая версия не найдена.")
        self.require_version_access(
            actor_id,
            version.assignee_user_id,
            version.work_order_status,
            version.edit_version.status,
        )
        return version

    async def get_change_set(
        self, work_order_id: UUID, edit_version_id: UUID, actor_id: UUID
    ) -> VersionChangeSetOut:
        version = await self.read_comparison(work_order_id, edit_version_id, actor_id)
        baseline = await self.default_state_repository.read_comparison_baseline(
            version.edit_version.default_state_id
        )
        with valid_readback():
            return project_version_changes(version, baseline)

    async def get_feature_baseline(
        self, work_order_id: UUID, edit_version_id: UUID, actor_id: UUID, feature_id: UUID
    ) -> FeatureBaselineOut:
        version = await self.read_comparison(work_order_id, edit_version_id, actor_id, feature_id)
        if (
            not version.features
            or not version.features[0].visible
            or version.features[0].feature_type != "line"
        ):
            raise WorkOrderApiError(404, "FEATURE_NOT_FOUND", "Линия рабочей версии не найдена.")
        baseline = await self.default_state_repository.read_geometry_baseline(
            default_state_id=version.edit_version.default_state_id,
            feature_id=feature_id,
        )
        with valid_readback():
            validate_baseline(version, baseline.state)
            if (
                baseline.feature is None
                or baseline.feature.feature_type != "line"
                or baseline.feature.feature_id != feature_id
            ):
                raise ValueError("Отсутствует исходная линия.")
            geometry = decode_geometry(baseline.feature.geometry_ewkb)
            return FeatureBaselineOut(
                feature_id=feature_id, baseline_geometry=geometry_to_geojson(geometry)
            )

    def map_response(self, version_map: EditVersionMapRow) -> EditVersionMapOut:
        if version_map.aoi is None or version_map.edit_version.draft_revision < 1:
            raise ValueError("Несогласованные данные рабочей версии.")

        aoi = MapAoiOut(
            id=version_map.aoi.id,
            name=version_map.aoi.name,
            description=version_map.aoi.description,
            geometry=version_map.aoi.geometry_data,
            extent=list(version_map.aoi.extent),
        )
        features = [
            MapFeatureOut(
                id=feature["id"],
                geometry=geometry_to_geojson(
                    decode_geometry(bytes.fromhex(feature["geometry_ewkb"]))
                ),
                properties=self.feature_properties(feature),
            )
            for feature in version_map.features_data
        ]
        return EditVersionMapOut(
            work_order=MapWorkOrderOut(
                id=version_map.work_order.id,
                code=version_map.work_order.code,
                title=version_map.work_order.title,
                description=version_map.work_order.description,
                status=version_map.work_order.status.value,
                scope=MapScopeOut(aoi=aoi),
                edit_version=MapEditVersionOut(
                    id=version_map.edit_version.id,
                    status=version_map.edit_version.status.value,
                    base_network_revision=version_map.edit_version.base_network_revision,
                    draft_version_token=str(version_map.edit_version.draft_revision),
                    features=MapFeatureCollectionOut(features=features),
                    associations=[
                        MapAssociationOut(
                            **{
                                **association,
                                "association_type": self.association_type_value(
                                    association["association_type"]
                                ),
                            }
                        )
                        for association in version_map.associations_data
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


@contextmanager
def valid_readback():
    try:
        yield
    except (AttributeError, KeyError, TypeError, ValueError, ValidationError) as exc:
        raise WorkOrderApiError(
            422,
            "WORKSPACE_CONTEXT_INVALID",
            "Данные рабочей версии не согласованы.",
        ) from exc
