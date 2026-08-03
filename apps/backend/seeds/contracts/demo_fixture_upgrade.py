import enum
from dataclasses import dataclass
from uuid import UUID

from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)


class DemoFixtureCopySource(str, enum.Enum):
    FEEDER = "feeder"
    DEFAULT_STATE = "default_state"
    EDIT_VERSION = "edit_version"


class DemoFixtureUpgradeError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoFixtureFeatureSnapshot:
    owner_id: UUID
    geometry_wkt: str
    geometry_type: str
    vertex_count: int
    network_version: int
    operation: EditVersionOperationState | None = None


@dataclass(frozen=True)
class DemoFixtureEditVersionSnapshot:
    edit_version_id: UUID
    default_state_id: UUID
    feature: DemoFixtureFeatureSnapshot | None


@dataclass(frozen=True)
class DemoFixtureHierarchy:
    feeder_id: UUID | None
    feeder_feature: DemoFixtureFeatureSnapshot | None
    work_order_id: UUID | None
    default_state_id: UUID | None
    default_feature: DemoFixtureFeatureSnapshot | None
    edit_versions: tuple[DemoFixtureEditVersionSnapshot, ...]


@dataclass(frozen=True)
class DemoFixtureGeometryUpdate:
    source: DemoFixtureCopySource
    owner_id: UUID
    geometry_wkt: str


@dataclass(frozen=True)
class DemoFixtureUpgradeResult:
    updates: tuple[DemoFixtureGeometryUpdate, ...]

    @property
    def updated_copy_count(self) -> int:
        return len(self.updates)

    @property
    def updated_sources(self) -> tuple[DemoFixtureCopySource, ...]:
        return tuple(update.source for update in self.updates)
