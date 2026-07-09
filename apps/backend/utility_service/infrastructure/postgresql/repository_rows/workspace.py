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
    aoi: WorkspaceAoiRow
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]
