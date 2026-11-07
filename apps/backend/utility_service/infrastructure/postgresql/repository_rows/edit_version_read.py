from dataclasses import dataclass
from typing import Any
from uuid import UUID

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)


@dataclass(frozen=True)
class MapWorkOrderRow:
    id: UUID
    code: str
    title: str
    description: str | None
    status: WorkOrderStatus
    assignee_user_id: UUID


@dataclass(frozen=True)
class VersionReadHeader:
    id: UUID
    status: EditVersionStatus
    base_network_revision: int
    draft_revision: int
    default_state_id: UUID


@dataclass(frozen=True)
class MapAoiRow:
    id: UUID
    name: str
    description: str | None
    geometry_data: dict[str, Any]
    extent: list[float]


@dataclass(frozen=True)
class EditVersionMapRow:
    work_order: MapWorkOrderRow
    edit_version: VersionReadHeader
    aoi: MapAoiRow | None
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]


@dataclass(frozen=True)
class CurrentDraftFeature:
    feature_id: UUID
    feature_type: str
    geometry_ewkb: str
    operation: str
    visible: bool


@dataclass(frozen=True)
class VersionComparisonRow:
    work_order_id: UUID
    assignee_user_id: UUID
    work_order_status: WorkOrderStatus
    edit_version: VersionReadHeader
    features: tuple[CurrentDraftFeature, ...]
