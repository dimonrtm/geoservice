from dataclasses import dataclass
from uuid import UUID
from typing import Literal

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.types import PreparedGeometry


class RepositoryProtocolError(RuntimeError):
    """Вызов repository вне выдавшей контекст транзакции."""


@dataclass(frozen=True)
class RepositoryRejection:
    code: str
    reason: str


@dataclass(frozen=True)
class LockedEditVersion:
    id: UUID
    work_order_id: UUID
    default_state_id: UUID
    base_network_revision: int
    draft_revision: int
    status: str
    policy: GeometryPolicy


@dataclass(frozen=True)
class EditGeometryFeature:
    feature_id: UUID
    feature_type: str
    operation: str | None
    network_version: int
    geometry_ewkb: bytes


@dataclass(frozen=True)
class EditGeometryDefaultState:
    id: UUID
    work_order_id: UUID
    base_network_revision: int
    status: str


@dataclass(frozen=True)
class EditGeometryContext:
    root: LockedEditVersion
    work_order_status: str
    assignee_user_id: UUID
    current: EditGeometryFeature
    baseline: EditGeometryFeature | None
    default_state: EditGeometryDefaultState | None
    aoi_ewkb: bytes | None
    other_changed_feature_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class PreparedGeometryHandle:
    context: EditGeometryContext
    prepared: PreparedGeometry


@dataclass(frozen=True)
class SpatialVerdict:
    shape_ok: bool
    nonempty: bool
    valid: bool
    simple: bool
    no_zero_segments: bool
    aoi_covered: bool
    aoi_valid: bool

    @property
    def geometry_valid(self) -> bool:
        return all(
            (
                self.shape_ok,
                self.nonempty,
                self.valid,
                self.simple,
                self.no_zero_segments,
            )
        )


@dataclass(frozen=True)
class ValidatedGeometryChange:
    context: EditGeometryContext
    before_ewkb: bytes
    after_ewkb: bytes
    operation: Literal["unchanged", "updated"]
    is_noop: bool
    vertex_index: int | None


@dataclass(frozen=True)
class GeometryWriteResult:
    changed: bool
    operation: Literal["unchanged", "updated"]
    before_ewkb: bytes
    after_ewkb: bytes
