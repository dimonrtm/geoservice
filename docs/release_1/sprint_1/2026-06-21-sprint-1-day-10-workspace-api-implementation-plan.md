# Sprint 1 Day 10 Workspace API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать backend-only Workspace API `GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace` с `AOI` в bounded context `work_order`.

**Architecture:** `WorkOrder` остается корнем aggregate: `scope.aoi`, active `EditVersion`, working `features` и `associations` живут в schema `work_order`. `utility_network` не владеет AOI и не является источником workspace features/associations; между bounded contexts нет FK. API читает workspace через `WorkspaceService`, который использует `WorkOrderRepository` и возвращает nested DTO.

**Tech Stack:** FastAPI, Pydantic v2 serialization aliases, async SQLAlchemy 2, GeoAlchemy2/PostGIS, Alembic, pytest.

---

## File Structure

- Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/aoi.py`: ORM model `AOI` in schema `work_order`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py`: export `AOI`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`: stop exporting `AOI`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py`: add `aoi_id` and relationship to `work_order.aois`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py`: create `work_order.aois`, add `work_orders.aoi_id`, remove `utility_network.aois` ownership.
- Modify `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`: assert new schema ownership and no cross-context FK.
- Modify `apps/backend/tests/integration_tests/test_edit_version_migration.py`: assert migration structure for `work_order.aois` and `work_orders.aoi_id`.
- Modify `apps/backend/seeds/specs/seed_utility_dataset_specs.py`: remove AOI from utility dataset spec.
- Modify `apps/backend/seeds/repositories/seed_utility_dataset_repository.py`: stop creating `utility_network.AOI`.
- Modify `apps/backend/seeds/repositories/seed_work_order_repository.py`: create/ensure `work_order.AOI` and pass `aoi_id` to `WorkOrder`.
- Modify `apps/backend/seeds/services/seed_work_order_service.py`: remove `get_first_aoi()` dependency from utility dataset repository; use work order AOI spec.
- Modify seed tests/integration tests under `apps/backend/seeds/tests/` and `apps/backend/tests/integration_tests/`.
- Create `apps/backend/utility_service/use_cases/schemas/workspace/`: response DTOs for `WorkOrderWorkspaceOut`, `WorkspaceAoiOut`, `WorkspaceEditVersionOut`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`: add workspace aggregate read method.
- Create `apps/backend/utility_service/use_cases/services/workspace_service.py`: authorization, state checks, filtering, DTO mapping.
- Modify `apps/backend/utility_service/use_cases/deps.py`: add `get_workspace_service`.
- Modify `apps/backend/utility_service/web_api/api/work_orders.py`: add nested workspace route.
- Modify `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`: add workspace route tests.
- Create `apps/backend/utility_service/use_cases/tests/test_workspace_service.py`: service unit tests.
- Modify `docs/release_1/sprint_1/README.md`: link this implementation plan.

## Task 1: Metadata Tests For AOI Move

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`

- [ ] **Step 1: Write failing metadata tests**

Replace `AOI` import from `utility_network` with `AOI` import from `work_order`, and add explicit assertions:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    DefaultStateStatus,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
    NetworkState,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    AOI,
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
```

Update `test_utility_network_package_exports_public_contract`:

```python
assert set(utility_network.__all__) == {
    "AssociationType",
    "DefaultState",
    "DefaultStateAssociation",
    "DefaultStateFeature",
    "DefaultStateStatus",
    "Feeder",
    "FeatureType",
    "NetworkAssociation",
    "NetworkFeature",
    "NetworkState",
}
```

Update `test_work_order_package_exports_public_contract`:

```python
assert set(work_order.__all__) == {
    "AOI",
    "EditVersion",
    "EditVersionAssociation",
    "EditVersionFeature",
    "EditVersionStatus",
    "WorkOrder",
    "WorkOrderStatus",
}
```

Add/replace AOI metadata test:

```python
def test_work_order_aoi_metadata_contains_geometry_guards() -> None:
    assert AOI.__tablename__ == "aois"
    assert AOI.__table__.schema == "work_order"
    assert {column.name for column in AOI.__table__.columns} == {
        "id",
        "name",
        "description",
        "geometry",
        "created_at",
        "updated_at",
    }
    assert {
        "ck_aois_geometry_not_empty",
        "ck_aois_geometry_valid",
        "ck_aois_geometry_srid",
        "ck_aois_geometry_type",
    }.issubset(constraint_names(AOI))
```

Add `aoi_id` expectations in `test_work_order_metadata_contains_aggregate_guards`:

```python
assert {column.name for column in WorkOrder.__table__.columns} == {
    "id",
    "code",
    "title",
    "description",
    "status",
    "aoi_id",
    "assignee_user_id",
    "created_by_user_id",
    "created_at",
    "updated_at",
}
assert WorkOrder.__table__.c.aoi_id.nullable is False
```

Update `test_work_order_has_no_cross_schema_foreign_keys`:

```python
assert foreign_key_targets(WorkOrder) == {"work_order.aois.id"}
```

- [ ] **Step 2: Run metadata tests and verify they fail**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: failures for missing `work_order.AOI`, stale `utility_network.AOI` export, and missing `WorkOrder.aoi_id`.

## Task 2: ORM Models And Exports

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/aoi.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`

- [ ] **Step 1: Create `work_order.AOI` model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/aoi.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from utility_service.infrastructure.postgresql.models.base import Base


class AOI(Base):
    __tablename__ = "aois"
    __table_args__ = (
        CheckConstraint("NOT ST_IsEmpty(geometry)", name="ck_aois_geometry_not_empty"),
        CheckConstraint("ST_IsValid(geometry)", name="ck_aois_geometry_valid"),
        CheckConstraint("ST_SRID(geometry) = 4326", name="ck_aois_geometry_srid"),
        CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')",
            name="ck_aois_geometry_type",
        ),
        Index("ix_aois_geometry", "geometry", postgresql_using="gist"),
        {"schema": "work_order"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
```

- [ ] **Step 2: Add `WorkOrder.aoi_id` and relationship**

Modify `work_order.py` imports:

```python
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.work_order.aoi import AOI
```

Add column before `assignee_user_id`:

```python
aoi_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(
        "work_order.aois.id",
        name="fk_work_orders_aoi",
        ondelete="RESTRICT",
    ),
    nullable=False,
)
```

Add relationship:

```python
aoi: Mapped[AOI] = relationship()
```

- [ ] **Step 3: Update package exports**

Modify `models/work_order/__init__.py`:

```python
from .aoi import AOI
from .edit_version import EditVersion, EditVersionStatus
from .edit_version_association import EditVersionAssociation
from .edit_version_feature import EditVersionFeature
from .work_order import WorkOrder, WorkOrderStatus

__all__ = [
    "AOI",
    "EditVersion",
    "EditVersionAssociation",
    "EditVersionFeature",
    "EditVersionStatus",
    "WorkOrder",
    "WorkOrderStatus",
]
```

Modify `models/utility_network/__init__.py`: remove `from .aoi import AOI` and remove `"AOI"` from `__all__`.

- [ ] **Step 4: Run metadata tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: PASS for metadata tests that do not require migration changes.

## Task 3: Migration Contract

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py`
- Modify: `apps/backend/tests/integration_tests/test_edit_version_migration.py`

- [ ] **Step 1: Add failing migration assertions**

In `test_edit_version_migration.py`, add required tables/constraints checks for:

```python
WORK_ORDER_TABLES = {
    "aois",
    "work_orders",
    "edit_versions",
    "edit_version_features",
    "edit_version_associations",
}

WORK_ORDER_CONSTRAINTS = {
    "ck_aois_geometry_not_empty",
    "ck_aois_geometry_valid",
    "ck_aois_geometry_srid",
    "ck_aois_geometry_type",
    "fk_work_orders_aoi",
    "fk_edit_versions_work_order",
    "uq_edit_versions_open_work_order",
}
```

Add an assertion that `utility_network.aois` is absent after `f2b3c4d5e6a7`:

```python
async def assert_utility_network_aoi_absent(connection):
    result = await connection.execute(
        sa.text(
            """
            SELECT to_regclass('utility_network.aois') IS NULL AS missing
            """
        )
    )
    assert result.scalar_one() is True
```

- [ ] **Step 2: Run migration test and verify it fails**

Run:

```powershell
cd apps/backend
python -m pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected without `RUN_DB_TESTS=1`: SKIPPED. With DB enabled: FAIL until migration is updated.

- [ ] **Step 3: Update repair migration**

In `f2b3c4d5e6a7_sprint1_schema_boundaries.py`, ensure upgrade drops legacy AOI after dependent objects are reset:

```python
op.execute(sa.text("DROP TABLE IF EXISTS utility_network.aois CASCADE"))
```

Create `work_order.aois` before `work_order.work_orders`:

```python
op.execute(
    sa.text(
        """
        CREATE TABLE IF NOT EXISTS work_order.aois (
            id uuid PRIMARY KEY,
            name varchar(200) NOT NULL,
            description text NULL,
            geometry geometry(GEOMETRY, 4326) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_aois_geometry_not_empty CHECK (NOT ST_IsEmpty(geometry)),
            CONSTRAINT ck_aois_geometry_valid CHECK (ST_IsValid(geometry)),
            CONSTRAINT ck_aois_geometry_srid CHECK (ST_SRID(geometry) = 4326),
            CONSTRAINT ck_aois_geometry_type
                CHECK (GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON'))
        )
        """
    )
)
op.execute(
    sa.text(
        """
        CREATE INDEX IF NOT EXISTS ix_aois_geometry
        ON work_order.aois
        USING gist (geometry)
        """
    )
)
```

Add `aoi_id uuid NOT NULL` and FK to `work_order.work_orders` creation:

```sql
aoi_id uuid NOT NULL,
CONSTRAINT fk_work_orders_aoi
    FOREIGN KEY (aoi_id)
    REFERENCES work_order.aois(id)
    ON DELETE RESTRICT,
```

Downgrade must drop `work_order.aois` after `work_order.work_orders`:

```python
op.drop_table("aois", schema="work_order")
```

- [ ] **Step 4: Run migration tests**

Run:

```powershell
cd apps/backend
python -m pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected without DB: SKIPPED. With `RUN_DB_TESTS=1`: PASS.

## Task 4: Seed AOI In WorkOrder Context

**Files:**
- Modify: `apps/backend/seeds/specs/seed_utility_dataset_specs.py`
- Modify: `apps/backend/seeds/specs/seed_work_order_specs.py`
- Modify: `apps/backend/seeds/repositories/seed_utility_dataset_repository.py`
- Modify: `apps/backend/seeds/repositories/seed_work_order_repository.py`
- Modify: `apps/backend/seeds/services/seed_work_order_service.py`
- Modify: `apps/backend/seeds/tests/test_seed_utility_dataset_service.py`
- Modify: `apps/backend/seeds/tests/test_seed_work_order_service.py`

- [ ] **Step 1: Write failing seed tests**

In `test_seed_utility_dataset_service.py`, assert utility seed no longer adds AOI:

```python
def test_utility_dataset_spec_no_longer_contains_aoi() -> None:
    assert not hasattr(UTILITY_DATASET_SPEC, "aoi")
```

In `test_seed_work_order_service.py`, assert AOI is passed to work order repository:

```python
def test_creates_work_order_with_aoi_scope() -> None:
    aoi = SimpleNamespace(id=uuid4())
    repository = repository_fake(
        get_work_order_by_code=None,
        ensure_aoi=aoi,
        create_work_order=SimpleNamespace(id=SEED_WORK_ORDER_SPEC.id),
    )
    # service setup continues with existing fake user and feeder
    # assert repository.create_work_order.await_args.kwargs["aoi_id"] == aoi.id
```

- [ ] **Step 2: Run seed tests and verify failure**

Run:

```powershell
cd apps/backend
python -m pytest seeds/tests/test_seed_utility_dataset_service.py seeds/tests/test_seed_work_order_service.py -q
```

Expected: FAIL until specs/repositories are updated.

- [ ] **Step 3: Move canonical AOI spec to work order spec**

In `seed_work_order_specs.py`, add:

```python
@dataclass(frozen=True)
class SeedWorkOrderAoiSpec:
    id: UUID
    name: str
    description: str | None
    geometry_wkt: str


SEED_WORK_ORDER_AOI_SPEC = SeedWorkOrderAoiSpec(
    id=UUID("19e7cc20-9171-468a-a69c-914662c17f02"),
    name="Рабочая область WO-001",
    description="Рабочая область для проверки участка фидера WO-001.",
    geometry_wkt="POLYGON((65.50 44.80, 65.54 44.80, 65.54 44.84, 65.50 44.84, 65.50 44.80))",
)
```

Remove AOI dataclass/spec field from `seed_utility_dataset_specs.py`.

- [ ] **Step 4: Stop utility dataset repository creating AOI**

In `seed_utility_dataset_repository.py`, remove `AOI` import and remove `aoi = AOI(...)`.

Change:

```python
self.session.add_all([aoi, feeder, *features])
```

to:

```python
self.session.add_all([feeder, *features])
```

Remove `get_first_aoi()`.

- [ ] **Step 5: Add work-order AOI ensure path**

In `seed_work_order_repository.py`, import:

```python
from geoalchemy2.elements import WKTElement
from utility_service.infrastructure.postgresql.models.work_order import AOI, WorkOrder
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_AOI_SPEC, SeedWorkOrderSpec
```

Add:

```python
async def ensure_aoi(self) -> AOI:
    existing = await self.session.get(AOI, SEED_WORK_ORDER_AOI_SPEC.id)
    if existing is not None:
        return existing
    aoi = AOI(
        id=SEED_WORK_ORDER_AOI_SPEC.id,
        name=SEED_WORK_ORDER_AOI_SPEC.name,
        description=SEED_WORK_ORDER_AOI_SPEC.description,
        geometry=WKTElement(SEED_WORK_ORDER_AOI_SPEC.geometry_wkt, srid=4326),
    )
    self.session.add(aoi)
    await self.session.flush()
    return aoi
```

Change `create_work_order` signature:

```python
async def create_work_order(
    self,
    spec: SeedWorkOrderSpec,
    *,
    aoi_id: UUID,
    assignee_user_id: UUID,
    created_by_user_id: UUID,
) -> WorkOrder:
```

Pass `aoi_id=aoi_id` into `WorkOrder(...)`.

- [ ] **Step 6: Update seed work order service**

In `seed_work_order_service.py`, remove `get_first_aoi()` call and use:

```python
aoi = await self.repository.ensure_aoi()
```

When creating work order:

```python
work_order = await self.repository.create_work_order(
    SEED_WORK_ORDER_SPEC,
    aoi_id=aoi.id,
    assignee_user_id=assignee.id,
    created_by_user_id=assignee.id,
)
```

For existing work order path, still call `await self.repository.ensure_aoi()` to keep seed idempotent.

- [ ] **Step 7: Run seed tests**

Run:

```powershell
cd apps/backend
python -m pytest seeds/tests/test_seed_utility_dataset_service.py seeds/tests/test_seed_work_order_service.py -q
```

Expected: PASS.

## Task 5: Workspace DTOs

**Files:**
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/aoi_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/association_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/edit_version_workspace_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/feature_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/work_order_workspace_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/workspace_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/workspace/__init__.py`
- Create/modify tests: `apps/backend/utility_service/use_cases/tests/test_workspace_schemas.py`

- [ ] **Step 1: Write schema tests**

Create `test_workspace_schemas.py`:

```python
from uuid import uuid4

from utility_service.use_cases.schemas.workspace import (
    WorkspaceAoiOut,
    WorkspaceEditVersionOut,
    WorkspaceFeatureCollectionOut,
    WorkspaceOut,
    WorkspaceWorkOrderOut,
)


def test_workspace_schema_uses_expected_wire_aliases() -> None:
    aoi = WorkspaceAoiOut(
        id=uuid4(),
        name="Рабочая область WO-001",
        description=None,
        geometry={"type": "Polygon", "coordinates": []},
        extent=[65.5, 44.8, 65.54, 44.84],
    )
    edit_version = WorkspaceEditVersionOut(
        id=uuid4(),
        status="open",
        base_network_revision=1,
        features=WorkspaceFeatureCollectionOut(features=[]),
        associations=[],
    )
    payload = WorkspaceOut(
        work_order=WorkspaceWorkOrderOut(
            id=uuid4(),
            code="WO-001",
            title="Проверка участка фидера",
            description=None,
            status="in_progress",
            aoi=aoi,
            edit_version=edit_version,
        )
    ).model_dump(by_alias=True)

    assert "workOrder" in payload
    assert payload["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    assert payload["workOrder"]["editVersion"]["baseNetworkRevision"] == 1
```

- [ ] **Step 2: Run schema test and verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_workspace_schemas.py -q
```

Expected: FAIL because schemas do not exist.

- [ ] **Step 3: Add workspace schemas**

Create `aoi_out.py`:

```python
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceAoiOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: str | None
    geometry: dict[str, Any]
    extent: list[float]
```

Create `edit_version_workspace_out.py`:

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.association_out import (
    WorkspaceAssociationOut,
)
from utility_service.use_cases.schemas.workspace.feature_out import (
    WorkspaceFeatureCollectionOut,
)


class WorkspaceEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    status: str
    base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
    features: WorkspaceFeatureCollectionOut
    associations: list[WorkspaceAssociationOut]
```

Create `work_order_workspace_out.py`:

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.aoi_out import WorkspaceAoiOut
from utility_service.use_cases.schemas.workspace.edit_version_workspace_out import (
    WorkspaceEditVersionOut,
)


class WorkspaceScopeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aoi: WorkspaceAoiOut


class WorkspaceWorkOrderOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    code: str
    title: str
    description: str | None
    status: str
    aoi: WorkspaceAoiOut = Field(serialization_alias="scope", exclude=True)
    edit_version: WorkspaceEditVersionOut = Field(serialization_alias="editVersion")

    @property
    def scope(self) -> WorkspaceScopeOut:
        return WorkspaceScopeOut(aoi=self.aoi)
```

If Pydantic property serialization does not include `scope`, replace with explicit field:

```python
scope: WorkspaceScopeOut
```

and construct `scope=WorkspaceScopeOut(aoi=aoi)` in service.

Create `workspace_out.py`:

```python
from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.workspace.work_order_workspace_out import (
    WorkspaceWorkOrderOut,
)


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    work_order: WorkspaceWorkOrderOut = Field(serialization_alias="workOrder")
```

Create `__init__.py` re-exporting all public classes.

- [ ] **Step 4: Run schema tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_workspace_schemas.py -q
```

Expected: PASS.

## Task 6: Repository Read Model For Workspace

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
- Create/modify tests: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository_workspace_sql.py` or integration test if repository unit style is not present.

- [ ] **Step 1: Add repository dataclasses**

In `work_order_repository.py`, add:

```python
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
```

- [ ] **Step 2: Add `get_workspace_aggregate`**

Use one SQLAlchemy statement with correlated JSONB subqueries:

```python
async def get_workspace_aggregate(
    self,
    *,
    work_order_id: UUID,
    edit_version_id: UUID,
) -> WorkspaceAggregateRow | None:
    # query WorkOrder + EditVersion + AOI; features filtered by ST_Intersects(AOI.geometry, feature.geometry)
    # associations filtered by both endpoints in filtered feature set
```

Implementation notes:

- Join `WorkOrder` -> `EditVersion` by `EditVersion.work_order_id == WorkOrder.id`.
- Join `AOI` by `WorkOrder.aoi_id == AOI.id`.
- Filter by both IDs.
- Feature subquery reads `EditVersionFeature` where `edit_version_id == EditVersion.id` and `ST_Intersects(AOI.geometry, EditVersionFeature.geometry)`.
- Association subquery reads `EditVersionAssociation` where both endpoint ids exist in the filtered feature subquery.
- Build feature properties with `assetCode`, `featureType`, `networkVersion`, `operation` plus JSONB properties.
- Return geometry via `ST_AsGeoJSON(...).cast(JSONB)`.
- Extent can be `[ST_XMin(box), ST_YMin(box), ST_XMax(box), ST_YMax(box)]` from `ST_Extent(AOI.geometry)` or `ST_Envelope` helpers.

- [ ] **Step 3: Add repository integration coverage**

Add an integration test in `tests/integration_tests/test_work_order_seed_chain_integration.py` after seed/open coverage:

```python
def test_seeded_workspace_aggregate_filters_features_by_work_order_aoi() -> None:
    # run seed chain
    # open edit version
    # repository.get_workspace_aggregate(work_order_id=..., edit_version_id=...)
    # assert aggregate.aoi.name == SEED_WORK_ORDER_AOI_SPEC.name
    # assert len(aggregate.features_data) == 19
    # assert len(aggregate.associations_data) == 9
```

- [ ] **Step 4: Run focused integration**

Run:

```powershell
cd apps/backend
python -m pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected without DB: SKIPPED. With DB: PASS after repository implementation.

## Task 7: WorkspaceService

**Files:**
- Create: `apps/backend/utility_service/use_cases/services/workspace_service.py`
- Create: `apps/backend/utility_service/use_cases/tests/test_workspace_service.py`

- [ ] **Step 1: Write service tests**

Create tests for:

```python
def test_editor_gets_workspace_for_assigned_open_edit_version() -> None: ...
def test_reviewer_is_denied() -> None: ...
def test_missing_workspace_returns_404() -> None: ...
def test_mismatched_work_order_and_edit_version_returns_404() -> None: ...
def test_workspace_state_conflict_returns_409() -> None: ...
def test_missing_aoi_returns_context_invalid() -> None: ...
```

Use `AsyncMock` repositories and `SimpleNamespace` rows. Expected codes:

```python
WorkspaceApiError(404, "EDIT_VERSION_NOT_FOUND", "Рабочая версия не найдена.")
WorkspaceApiError(409, "EDIT_VERSION_STATE_CONFLICT", "Состояние рабочей версии не допускает операцию.")
WorkspaceApiError(422, "WORKSPACE_CONTEXT_INVALID", "Workspace невозможно сформировать из текущих данных.")
```

- [ ] **Step 2: Run service tests and verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_workspace_service.py -q
```

Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement `WorkspaceService`**

Create `workspace_service.py`:

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import WorkOrderRepository
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.workspace import WorkspaceOut


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
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
        actor_id: UUID,
    ) -> WorkspaceOut:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None or actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(403, "ROLE_NOT_ALLOWED", "Роль пользователя не допускает операцию.")

        aggregate = await self.work_order_repository.get_workspace_aggregate(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
        if aggregate is None or aggregate.work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(404, "EDIT_VERSION_NOT_FOUND", "Рабочая версия не найдена.")

        if (
            aggregate.work_order.status is not WorkOrderStatus.IN_PROGRESS
            or aggregate.edit_version.status is not EditVersionStatus.OPEN
        ):
            raise WorkOrderApiError(
                409,
                "EDIT_VERSION_STATE_CONFLICT",
                "Состояние рабочей версии не допускает операцию.",
            )

        return map_workspace_aggregate(aggregate)
```

Implement `map_workspace_aggregate(...)` in the same file or a private helper to keep service readable.

- [ ] **Step 4: Run service tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_workspace_service.py -q
```

Expected: PASS.

## Task 8: Workspace API Route

**Files:**
- Modify: `apps/backend/utility_service/use_cases/deps.py`
- Modify: `apps/backend/utility_service/web_api/api/work_orders.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Write API tests**

Extend `build_app` in `test_work_orders_api.py` to override `get_workspace_service`.

Add:

```python
def test_get_workspace_returns_nested_work_order_payload() -> None:
    work_order_id = uuid4()
    edit_version_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    workspace_service = AsyncMock()
    workspace_service.get_workspace.return_value = workspace_response(work_order_id, edit_version_id)

    response = TestClient(build_app(auth_service, edit_version_service, workspace_service)).get(
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["workOrder"]["id"] == str(work_order_id)
    assert response.json()["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    workspace_service.get_workspace.assert_awaited_once_with(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        actor_id=user_id,
    )
```

Add mismatch/service error test:

```python
def test_workspace_service_404_is_structured() -> None:
    workspace_service.get_workspace.side_effect = WorkOrderApiError(
        404,
        "EDIT_VERSION_NOT_FOUND",
        "Рабочая версия не найдена.",
    )
```

- [ ] **Step 2: Run API tests and verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: FAIL because dependency/route does not exist.

- [ ] **Step 3: Add dependency**

In `deps.py` import `WorkspaceService` and add:

```python
def get_workspace_service(
    session: AsyncSession = Depends(get_session),
) -> WorkspaceService:
    return WorkspaceService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
    )
```

- [ ] **Step 4: Add route**

In `work_orders.py`:

```python
from utility_service.use_cases.deps import get_edit_version_service, get_workspace_service
from utility_service.use_cases.schemas.workspace import WorkspaceOut
from utility_service.use_cases.services.workspace_service import WorkspaceService
```

Add:

```python
@work_orders_router.get(
    "/{work_order_id}/edit-versions/{edit_version_id}/workspace",
    response_model=WorkspaceOut,
)
async def get_workspace(
    work_order_id: UUID,
    edit_version_id: UUID,
    user: Any = Depends(require_editor),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceOut:
    return await workspace_service.get_workspace(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        actor_id=user.id,
    )
```

- [ ] **Step 5: Run API tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

## Task 9: Focused Integration And Quality Gates

**Files:**
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
- No production code unless a prior task missed an integration issue.

- [ ] **Step 1: Add HTTP-level integration acceptance if test harness supports it**

If existing integration helpers can create a FastAPI client against real DB, add:

```python
def test_seed_chain_workspace_api_returns_open_edit_version_workspace() -> None:
    # clean seed chain
    # run seed chain
    # login/open edit version
    # GET nested workspace route
    # assert workOrder.code == "WO-001"
    # assert scope.aoi.name == SEED_WORK_ORDER_AOI_SPEC.name
    # assert len(features) == 19
    # assert len(associations) == 9
```

If no real API client harness exists, keep repository/service integration from Task 6 as the focused DB acceptance and do not invent a new test harness.

- [ ] **Step 2: Run focused backend tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py \
  utility_service/use_cases/tests/test_workspace_schemas.py \
  utility_service/use_cases/tests/test_workspace_service.py \
  utility_service/web_api/tests/test_work_orders_api.py \
  seeds/tests/test_seed_utility_dataset_service.py \
  seeds/tests/test_seed_work_order_service.py -q
```

Expected: PASS.

- [ ] **Step 3: Run integration tests**

Run:

```powershell
cd apps/backend
python -m pytest tests/integration_tests/test_edit_version_migration.py tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected without DB: SKIPPED. With `RUN_DB_TESTS=1`: PASS.

- [ ] **Step 4: Run broad backend test suite**

Run:

```powershell
cd apps/backend
python -m pytest -q
```

Expected: PASS, except DB integration tests may SKIP when `RUN_DB_TESTS` is not enabled.

## Task 10: Documentation Sync Decision

**Files:**
- Review only: `docs/release_1/sprint_1/2026-06-21-sprint-1-day-10-workspace-api-design.md`
- Optional after implementation: `Code_wiki/архитектура/data_model.md`, `Code_wiki/архитектура/api_and_realtime.md`, only via `/ingest repository-change` when durable technical knowledge exists.

- [ ] **Step 1: Check whether repository-change ingest is required**

After implementation, answer:

```text
Did implementation create new durable technical knowledge not already preserved
by design, implementation plan, code, tests, or existing Code_wiki?
```

Expected for this task: likely yes, because AOI ownership moves from `utility_network` to `work_order` and Workspace API becomes public backend contract. If so, run `/ingest repository-change` after code is complete. If Code_wiki already captured the exact final implementation through a prior ingest, do not duplicate it.

- [ ] **Step 2: Do not update memory unless criteria are met**

Do not create agent memory for simple task completion, changed files, or test logs. Consider memory only if a non-obvious bug root cause or durable operational constraint appears during implementation.

## Plan Self-Review

- Spec coverage: covered AOI ownership, no cross-context FK, storage/migration, seed shift, nested route, no auto-open, working feature/association source, errors, and tests.
- Placeholder scan: no `TBD`/`TODO`; Task 6 has a compact repository method outline because SQL expression is lengthy, but includes exact query semantics and acceptance tests.
- Type consistency: uses `work_order_id`, `edit_version_id`, `base_network_revision`, `WorkspaceOut`, and `WorkOrderApiError` consistently with existing code style.

## Execution Handoff

Plan complete and saved to `docs/release_1/sprint_1/2026-06-21-sprint-1-day-10-workspace-api-implementation-plan.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.
