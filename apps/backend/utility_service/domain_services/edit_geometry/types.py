from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID


Position = tuple[Decimal, Decimal]


@dataclass(frozen=True)
class GeometryValue:
    type: Literal["Point", "LineString"]
    coordinates: tuple[Position, ...]
    srid: int = 4326


class GeometryRuleError(ValueError):
    def __init__(
        self,
        code: str,
    ):
        self.code = code
        super().__init__(f"Нарушено правило изменения геометрии: {code}.")


class InvalidGeometryContext(ValueError):
    pass


@dataclass(frozen=True)
class PreparedGeometry:
    representation: Literal["baseline_aligned", "unmatched_structure"]
    geometry: GeometryValue
    vertex_index: int | None
    rejection_code: str | None


@dataclass(frozen=True)
class TransitionResult:
    operation: Literal["unchanged", "updated"]
    is_noop: bool
    vertex_index: int | None


@dataclass(frozen=True)
class FingerprintContext:
    work_order_id: UUID
    edit_version_id: UUID
    feature_id: UUID
    actor_user_id: UUID
    default_state_id: UUID
    base_network_revision: int
    draft_version_token: str
