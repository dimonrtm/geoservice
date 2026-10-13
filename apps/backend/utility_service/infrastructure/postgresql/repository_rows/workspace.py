from dataclasses import dataclass
from typing import Any
from uuid import UUID

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)


@dataclass(frozen=True)
class WorkspaceWorkOrderRow:
    id: UUID
    code: str
    title: str
    description: str | None
    status: WorkOrderStatus
    assignee_user_id: UUID


@dataclass(frozen=True)
class WorkspaceEditVersionRow:
    id: UUID
    status: EditVersionStatus
    base_network_revision: int
    draft_revision: int
    default_state_id: UUID


@dataclass(frozen=True)
class WorkspaceBaselineStateRow:
    id: UUID
    work_order_id: UUID
    base_network_revision: int
    status: str


@dataclass(frozen=True)
class WorkspaceDraftFeaturePairRow:
    feature_id: UUID
    current_feature_type: str | None
    baseline_feature_type: str | None
    current_geometry_ewkb: str | None
    baseline_geometry_ewkb: str | None
    operation: str | None
    visible: bool


@dataclass(frozen=True)
class WorkspaceAoiRow:
    id: UUID
    name: str
    description: str | None
    geometry_data: dict[str, Any]
    extent: list[float]


@dataclass(frozen=True)
class WorkspaceAggregateRow:
    work_order: WorkspaceWorkOrderRow
    edit_version: WorkspaceEditVersionRow
    aoi: WorkspaceAoiRow | None
    baseline_state: WorkspaceBaselineStateRow | None
    draft_feature_pairs: tuple[WorkspaceDraftFeaturePairRow, ...]
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]
