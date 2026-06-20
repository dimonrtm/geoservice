# Data Model Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перевести backend data model на схемы `"user"`, `utility_network` и `work_order`, создать deep copy `EditVersion` от per-WorkOrder `DefaultState`, сохранить deploy path и CI.

**Architecture:** Изменение выполняется вертикально: сначала metadata tests фиксируют новые границы, затем добавляются ORM-модели и reset-style migration, после этого переподключаются repositories, services, seed и API schemas. `EditVersion` является частью агрегата `WorkOrder`, поэтому отдельного `EditVersionRepository` нет; чтение `DefaultState`/baseline rows идет через `DefaultStateRepository`, а запись `work_order.*` - через `WorkOrderRepository`. Cross-schema FK между `"user"`, `utility_network` и `work_order` запрещены.

`DefaultStateRepository` читает active `DefaultState` aggregate одним SQL round
trip: строку `default_states`, features и associations через независимые JSONB
aggregation subqueries. Это сохраняет service boundary и не создает
`features x associations` row explosion. Текст SQL хранится в
`utility_service/infrastructure/postgresql/sql/default_state_aggregate.sql` и
загружается один раз в module-level SQLAlchemy statement.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, PostgreSQL/PostGIS, pytest.

**Repo Rule:** Не выполнять `git add` и `git commit`, пока пользователь явно не попросит. План содержит checkpoint steps вместо commit steps.

---

## Source Spec

Design spec: `docs/release_1/sprint_1/2026-06-20-sprint-1-data-model-boundaries-design.md`

Key decisions from spec:

- `users` живет в schema `"user"`.
- `WorkOrder`, `EditVersion`, `EditVersionFeature`, `EditVersionAssociation` живут в schema `work_order`.
- `DefaultState`, `DefaultStateFeature`, `DefaultStateAssociation`, `NetworkState` живут в schema `utility_network`.
- `DefaultState.status` поддерживает только `active`.
- Refresh `DefaultState` закладывается как метод, но automatic trigger не добавляется.
- Старые `utility_network.work_orders` и `utility_network.edit_versions` удаляются без compatibility views.
- `baseRevision` не поддерживается; API response использует `baseNetworkRevision`.
- Существующие demo workflow данные не переносятся; seed пересоздает данные после structural migration.

## File Structure

Create:

- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py` - public exports for work-order aggregate models.
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py` - `WorkOrder`, `WorkOrderStatus`.
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py` - `EditVersion`, `EditVersionStatus`.
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py` - working feature copy.
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_association.py` - working association copy.
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/network_state.py` - global published-network revision.
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_feature.py` - baseline feature copy.
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_association.py` - baseline association copy.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b4c6d8e9a1_data_model_boundaries.py` - reset-style structural migration.

Modify:

- `apps/backend/utility_service/infrastructure/postgresql/models/user.py` - add `schema="user"`.
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py` - change singleton into per-WorkOrder baseline.
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py` - remove work-order exports, add `NetworkState` and baseline copy exports.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py` - import new models.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py` - aggregate repository for `WorkOrder` and nested `EditVersion`.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py` - `DefaultState` lookup/create/refresh helper methods.
- `apps/backend/utility_service/use_cases/deps.py` - stop wiring `EditVersionRepository`.
- `apps/backend/utility_service/use_cases/services/edit_version_service.py` - use aggregate `WorkOrderRepository`.
- `apps/backend/utility_service/use_cases/schemas/edit_version/edit_version_out.py` - expose `baseNetworkRevision`.
- `apps/backend/utility_service/web_api/api/work_orders.py` - response mapping uses `base_network_revision`.
- `apps/backend/seeds/repositories/seed_work_order_repository.py` - create new `WorkOrder` shape.
- `apps/backend/seeds/services/seed_work_order_service.py` - create `DefaultState` after `WorkOrder`.
- `apps/backend/tests/test_compose_startup_contract.py` - include default state seed responsibility if startup command changes.

Delete:

- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py`
- `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py`
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`

Tests to update:

- `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`
- `apps/backend/utility_service/infrastructure/tests/test_user_role_model.py`
- `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
- `apps/backend/utility_service/use_cases/tests/test_work_order_service.py`
- `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`
- `apps/backend/seeds/tests/test_seed_work_order_service.py`
- `apps/backend/tests/integration_tests/test_edit_version_migration.py`
- `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

---

### Task 1: Lock New ORM Boundary Tests

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`
- Modify: `apps/backend/utility_service/infrastructure/tests/test_user_role_model.py`

- [ ] **Step 1: Update imports in metadata tests to the new package boundary**

Replace the top import block in `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py` with:

```python
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
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
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
```

- [ ] **Step 2: Replace package export test**

Replace `test_utility_network_package_exports_public_contract` with:

```python
def test_utility_network_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import utility_network

    assert set(utility_network.__all__) == {
        "AOI",
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


def test_work_order_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import work_order

    assert set(work_order.__all__) == {
        "EditVersion",
        "EditVersionAssociation",
        "EditVersionFeature",
        "EditVersionStatus",
        "WorkOrder",
        "WorkOrderStatus",
    }
```

- [ ] **Step 3: Add schema ownership and cross-schema FK tests**

Add these tests after the package export tests:

```python
def foreign_key_targets(model: type) -> set[str]:
    return {
        element.target_fullname
        for constraint in model.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
    }


def test_user_model_uses_user_schema() -> None:
    assert User.__tablename__ == "users"
    assert User.__table__.schema == "user"


def test_work_order_models_use_work_order_schema() -> None:
    assert WorkOrder.__table__.schema == "work_order"
    assert EditVersion.__table__.schema == "work_order"
    assert EditVersionFeature.__table__.schema == "work_order"
    assert EditVersionAssociation.__table__.schema == "work_order"


def test_new_utility_baseline_models_use_utility_network_schema() -> None:
    assert NetworkState.__table__.schema == "utility_network"
    assert DefaultState.__table__.schema == "utility_network"
    assert DefaultStateFeature.__table__.schema == "utility_network"
    assert DefaultStateAssociation.__table__.schema == "utility_network"


def test_work_order_has_no_cross_schema_foreign_keys() -> None:
    assert foreign_key_targets(WorkOrder) == set()
    assert foreign_key_targets(EditVersion) == {"work_order.work_orders.id"}
    assert foreign_key_targets(EditVersionFeature) == {"work_order.edit_versions.id"}
    assert foreign_key_targets(EditVersionAssociation) == {
        "work_order.edit_versions.id",
        "work_order.edit_version_features.edit_version_id",
        "work_order.edit_version_features.feature_id",
    }


def test_default_state_uses_plain_work_order_reference() -> None:
    assert "work_order_id" in DefaultState.__table__.c
    assert "work_order.work_orders.id" not in foreign_key_targets(DefaultState)
```

- [ ] **Step 4: Replace old WorkOrder metadata tests**

Replace `test_work_order_metadata_contains_assignment_guards`,
`test_work_order_foreign_keys_are_restrictive_and_schema_qualified`, and
`test_work_order_declares_lookup_indexes` with:

```python
def test_work_order_metadata_contains_assignment_guards() -> None:
    assert WorkOrder.__tablename__ == "work_orders"
    assert WorkOrder.__table__.schema == "work_order"
    assert {column.name for column in WorkOrder.__table__.columns} == {
        "id",
        "code",
        "title",
        "description",
        "status",
        "assignee_user_id",
        "created_at",
        "updated_at",
    }
    assert {
        "uq_work_orders_code",
        "ck_work_orders_status",
    }.issubset(constraint_names(WorkOrder))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in WorkOrder.__table__.constraints
    )


def test_work_order_declares_lookup_indexes() -> None:
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in WorkOrder.__table__.indexes
    }

    assert indexes == {
        "ix_work_orders_assignee_user_id": ("assignee_user_id",),
        "ix_work_orders_status": ("status",),
    }
```

- [ ] **Step 5: Replace old DefaultState metadata test**

Replace `test_default_state_metadata_contains_singleton_revision_guards` with:

```python
def test_network_state_metadata_contains_revision_guards() -> None:
    assert NetworkState.__tablename__ == "network_states"
    assert NetworkState.__table__.schema == "utility_network"
    assert {column.name for column in NetworkState.__table__.columns} == {
        "id",
        "name",
        "current_revision",
        "created_at",
        "updated_at",
    }
    assert {
        "uq_network_states_name",
        "ck_network_states_current_revision_positive",
    }.issubset(constraint_names(NetworkState))


def test_default_state_metadata_contains_work_order_baseline_guards() -> None:
    assert DefaultState.__tablename__ == "default_states"
    assert DefaultState.__table__.schema == "utility_network"
    assert {column.name for column in DefaultState.__table__.columns} == {
        "id",
        "work_order_id",
        "network_revision",
        "source_feeder_id",
        "source_aoi_id",
        "status",
        "created_at",
        "updated_at",
    }
    assert DefaultState.__table__.c.network_revision.default.arg == 1
    assert str(DefaultState.__table__.c.network_revision.server_default.arg) == "1"
    assert {
        "uq_default_states_work_order_id",
        "ck_default_states_network_revision_positive",
        "ck_default_states_status",
    }.issubset(constraint_names(DefaultState))


def test_default_state_status_values_are_stable_strings() -> None:
    assert {item.value for item in DefaultStateStatus} == {"active"}
```

- [ ] **Step 6: Replace old EditVersion metadata tests**

Replace `test_edit_version_metadata_contains_open_version_guards`,
`test_edit_version_foreign_keys_are_restrictive_and_schema_qualified`, and
`test_edit_version_declares_partial_open_unique_index` with:

```python
def test_edit_version_metadata_contains_open_version_guards() -> None:
    assert EditVersion.__tablename__ == "edit_versions"
    assert EditVersion.__table__.schema == "work_order"
    assert {column.name for column in EditVersion.__table__.columns} == {
        "id",
        "work_order_id",
        "owner_user_id",
        "default_state_id",
        "base_network_revision",
        "status",
        "created_at",
        "last_opened_at",
    }
    assert EditVersion.__table__.c.base_network_revision.default.arg == 1
    assert str(EditVersion.__table__.c.base_network_revision.server_default.arg) == "1"
    assert {
        "ck_edit_versions_base_network_revision_positive",
        "ck_edit_versions_status",
    }.issubset(constraint_names(EditVersion))


def test_edit_version_foreign_keys_are_internal_to_work_order_schema() -> None:
    foreign_keys = [
        constraint
        for constraint in EditVersion.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 1
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {"work_order.work_orders.id"}


def test_edit_version_declares_partial_open_unique_index() -> None:
    indexes = {index.name: index for index in EditVersion.__table__.indexes}

    assert "uq_edit_versions_open_work_order" in indexes
    index = indexes["uq_edit_versions_open_work_order"]
    assert tuple(column.name for column in index.columns) == ("work_order_id",)
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == "status = 'open'"
```

- [ ] **Step 7: Add copy table metadata tests**

Add:

```python
def test_default_state_feature_metadata_contains_copy_guards() -> None:
    assert DefaultStateFeature.__tablename__ == "default_state_features"
    assert DefaultStateFeature.__table__.schema == "utility_network"
    assert {column.name for column in DefaultStateFeature.__table__.columns} == {
        "default_state_id",
        "feature_id",
        "feeder_id",
        "asset_code",
        "feature_type",
        "geometry",
        "name",
        "description",
        "properties",
        "version",
        "created_at",
        "updated_at",
    }
    assert {
        "ck_default_state_features_geometry_not_empty",
        "ck_default_state_features_geometry_valid",
        "ck_default_state_features_geometry_srid",
        "ck_default_state_features_geometry_matches_type",
        "ck_default_state_features_version_positive",
    }.issubset(constraint_names(DefaultStateFeature))


def test_edit_version_feature_metadata_contains_copy_guards() -> None:
    assert EditVersionFeature.__tablename__ == "edit_version_features"
    assert EditVersionFeature.__table__.schema == "work_order"
    assert {column.name for column in EditVersionFeature.__table__.columns} == {
        "edit_version_id",
        "feature_id",
        "feeder_id",
        "asset_code",
        "feature_type",
        "geometry",
        "name",
        "description",
        "properties",
        "base_version",
        "version",
        "operation_state",
        "created_at",
        "updated_at",
    }
    assert {
        "ck_edit_version_features_geometry_not_empty",
        "ck_edit_version_features_geometry_valid",
        "ck_edit_version_features_geometry_srid",
        "ck_edit_version_features_geometry_matches_type",
        "ck_edit_version_features_base_version_positive",
        "ck_edit_version_features_version_positive",
        "ck_edit_version_features_operation_state",
    }.issubset(constraint_names(EditVersionFeature))
```

- [ ] **Step 8: Run metadata tests and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: FAIL with import errors for `models.work_order` or assertion failures for old schema metadata.

- [ ] **Step 9: Checkpoint**

Do not run `git add` or `git commit`. Record in the task tracker that metadata boundary tests are failing for the expected reason.

---

### Task 2: Implement ORM Models And Package Boundaries

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_association.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/network_state.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_feature.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_association.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/user.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
- Deleted in this task: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py`
- Deleted in this task: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py`

- [ ] **Step 1: Add user schema to the existing user model**

In `apps/backend/utility_service/infrastructure/postgresql/models/user.py`, add:

```python
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "user"}
```

Keep existing columns unchanged.

- [ ] **Step 2: Create work_order package exports**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py`:

```python
from .edit_version import EditVersion, EditVersionStatus
from .edit_version_association import EditVersionAssociation, EditVersionOperationState
from .edit_version_feature import EditVersionFeature
from .work_order import WorkOrder, WorkOrderStatus

__all__ = [
    "EditVersion",
    "EditVersionAssociation",
    "EditVersionFeature",
    "EditVersionOperationState",
    "EditVersionStatus",
    "WorkOrder",
    "WorkOrderStatus",
]
```

- [ ] **Step 3: Create WorkOrder ORM model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py`:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base


class WorkOrderStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        UniqueConstraint("code", name="uq_work_orders_code"),
        CheckConstraint(
            "status IN ('assigned', 'in_progress')",
            name="ck_work_orders_status",
        ),
        Index("ix_work_orders_assignee_user_id", "assignee_user_id"),
        Index("ix_work_orders_status", "status"),
        {"schema": "work_order"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WorkOrderStatus] = mapped_column(
        SAEnum(
            WorkOrderStatus,
            name="work_order_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=WorkOrderStatus.ASSIGNED,
        server_default=WorkOrderStatus.ASSIGNED.value,
    )
    assignee_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    edit_versions = relationship("EditVersion", back_populates="work_order")
```

- [ ] **Step 4: Create EditVersion ORM model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py`:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base

if TYPE_CHECKING:
    from utility_service.infrastructure.postgresql.models.work_order.work_order import WorkOrder


class EditVersionStatus(str, enum.Enum):
    OPEN = "open"


class EditVersion(Base):
    __tablename__ = "edit_versions"
    __table_args__ = (
        CheckConstraint(
            "base_network_revision >= 1",
            name="ck_edit_versions_base_network_revision_positive",
        ),
        CheckConstraint("status IN ('open')", name="ck_edit_versions_status"),
        Index(
            "uq_edit_versions_open_work_order",
            "work_order_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        {"schema": "work_order"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_order.work_orders.id", name="fk_edit_versions_work_order", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    default_state_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_network_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    status: Mapped[EditVersionStatus] = mapped_column(
        SAEnum(
            EditVersionStatus,
            name="edit_version_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=EditVersionStatus.OPEN,
        server_default=EditVersionStatus.OPEN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    work_order: Mapped[WorkOrder] = relationship(back_populates="edit_versions")
    features = relationship("EditVersionFeature", back_populates="edit_version")
    associations = relationship("EditVersionAssociation", back_populates="edit_version")
```

- [ ] **Step 5: Create EditVersionFeature ORM model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py`:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_feature import FeatureType


class EditVersionOperationState(str, enum.Enum):
    UNCHANGED = "unchanged"
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"


class EditVersionFeature(Base):
    __tablename__ = "edit_version_features"
    __table_args__ = (
        CheckConstraint("NOT ST_IsEmpty(geometry)", name="ck_edit_version_features_geometry_not_empty"),
        CheckConstraint("ST_IsValid(geometry)", name="ck_edit_version_features_geometry_valid"),
        CheckConstraint("ST_SRID(geometry) = 4326", name="ck_edit_version_features_geometry_srid"),
        CheckConstraint(
            "((feature_type IN ('junction', 'device') AND GeometryType(geometry) = 'POINT') "
            "OR (feature_type = 'line' AND GeometryType(geometry) = 'LINESTRING'))",
            name="ck_edit_version_features_geometry_matches_type",
        ),
        CheckConstraint(
            "base_version IS NULL OR base_version >= 1",
            name="ck_edit_version_features_base_version_positive",
        ),
        CheckConstraint("version >= 1", name="ck_edit_version_features_version_positive"),
        CheckConstraint(
            "operation_state IN ('unchanged', 'new', 'modified', 'deleted')",
            name="ck_edit_version_features_operation_state",
        ),
        {"schema": "work_order"},
    )

    edit_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_order.edit_versions.id", name="fk_edit_version_features_edit_version", ondelete="CASCADE"),
        primary_key=True,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    feeder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SAEnum(
            FeatureType,
            name="edit_version_feature_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    geometry: Mapped[object] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    base_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    operation_state: Mapped[EditVersionOperationState] = mapped_column(
        SAEnum(
            EditVersionOperationState,
            name="edit_version_operation_state",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=EditVersionOperationState.UNCHANGED,
        server_default=EditVersionOperationState.UNCHANGED.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    edit_version = relationship("EditVersion", back_populates="features")
```

- [ ] **Step 6: Create EditVersionAssociation ORM model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_association.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, ForeignKeyConstraint, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_association import AssociationType
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import EditVersionOperationState


class EditVersionAssociation(Base):
    __tablename__ = "edit_version_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["edit_version_id", "from_feature_id"],
            ["work_order.edit_version_features.edit_version_id", "work_order.edit_version_features.feature_id"],
            name="fk_edit_version_associations_from_feature",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["edit_version_id", "to_feature_id"],
            ["work_order.edit_version_features.edit_version_id", "work_order.edit_version_features.feature_id"],
            name="fk_edit_version_associations_to_feature",
            ondelete="CASCADE",
        ),
        CheckConstraint("from_feature_id <> to_feature_id", name="ck_edit_version_associations_no_self_reference"),
        CheckConstraint("base_version IS NULL OR base_version >= 1", name="ck_edit_version_associations_base_version_positive"),
        CheckConstraint("version >= 1", name="ck_edit_version_associations_version_positive"),
        CheckConstraint(
            "operation_state IN ('unchanged', 'new', 'modified', 'deleted')",
            name="ck_edit_version_associations_operation_state",
        ),
        {"schema": "work_order"},
    )

    edit_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_order.edit_versions.id", name="fk_edit_version_associations_edit_version", ondelete="CASCADE"),
        primary_key=True,
    )
    association_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    feeder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    association_type: Mapped[AssociationType] = mapped_column(
        SAEnum(
            AssociationType,
            name="edit_version_association_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    from_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    operation_state: Mapped[EditVersionOperationState] = mapped_column(
        SAEnum(
            EditVersionOperationState,
            name="edit_version_association_operation_state",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=EditVersionOperationState.UNCHANGED,
        server_default=EditVersionOperationState.UNCHANGED.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    edit_version = relationship("EditVersion", back_populates="associations")
```

- [ ] **Step 7: Create NetworkState and update DefaultState**

Create `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/network_state.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from utility_service.infrastructure.postgresql.models.base import Base


class NetworkState(Base):
    __tablename__ = "network_states"
    __table_args__ = (
        UniqueConstraint("name", name="uq_network_states_name"),
        CheckConstraint("current_revision >= 1", name="ck_network_states_current_revision_positive"),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

Replace `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py` with:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base


class DefaultStateStatus(str, enum.Enum):
    ACTIVE = "active"


class DefaultState(Base):
    __tablename__ = "default_states"
    __table_args__ = (
        UniqueConstraint("work_order_id", name="uq_default_states_work_order_id"),
        CheckConstraint("network_revision >= 1", name="ck_default_states_network_revision_positive"),
        CheckConstraint("status IN ('active')", name="ck_default_states_status"),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    network_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    source_feeder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_aoi_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[DefaultStateStatus] = mapped_column(
        SAEnum(
            DefaultStateStatus,
            name="default_state_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
        default=DefaultStateStatus.ACTIVE,
        server_default=DefaultStateStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    features = relationship("DefaultStateFeature", back_populates="default_state")
    associations = relationship("DefaultStateAssociation", back_populates="default_state")
```

- [ ] **Step 8: Create baseline copy ORM models**

Create `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_feature.py` with this file content:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_feature import FeatureType


class DefaultStateFeature(Base):
    __tablename__ = "default_state_features"
    __table_args__ = (
        CheckConstraint("NOT ST_IsEmpty(geometry)", name="ck_default_state_features_geometry_not_empty"),
        CheckConstraint("ST_IsValid(geometry)", name="ck_default_state_features_geometry_valid"),
        CheckConstraint("ST_SRID(geometry) = 4326", name="ck_default_state_features_geometry_srid"),
        CheckConstraint(
            "((feature_type IN ('junction', 'device') AND GeometryType(geometry) = 'POINT') "
            "OR (feature_type = 'line' AND GeometryType(geometry) = 'LINESTRING'))",
            name="ck_default_state_features_geometry_matches_type",
        ),
        CheckConstraint("version >= 1", name="ck_default_state_features_version_positive"),
        {"schema": "utility_network"},
    )

    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("utility_network.default_states.id", name="fk_default_state_features_default_state", ondelete="CASCADE"),
        primary_key=True,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    feeder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SAEnum(
            FeatureType,
            name="default_state_feature_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    geometry: Mapped[object] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    default_state = relationship("DefaultState", back_populates="features")
```

Create `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state_association.py` with this file content:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, ForeignKeyConstraint, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base
from utility_service.infrastructure.postgresql.models.utility_network.network_association import AssociationType


class DefaultStateAssociation(Base):
    __tablename__ = "default_state_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["default_state_id", "from_feature_id"],
            ["utility_network.default_state_features.default_state_id", "utility_network.default_state_features.feature_id"],
            name="fk_default_state_associations_from_feature",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["default_state_id", "to_feature_id"],
            ["utility_network.default_state_features.default_state_id", "utility_network.default_state_features.feature_id"],
            name="fk_default_state_associations_to_feature",
            ondelete="CASCADE",
        ),
        CheckConstraint("from_feature_id <> to_feature_id", name="ck_default_state_associations_no_self_reference"),
        CheckConstraint("version >= 1", name="ck_default_state_associations_version_positive"),
        {"schema": "utility_network"},
    )

    default_state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("utility_network.default_states.id", name="fk_default_state_associations_default_state", ondelete="CASCADE"),
        primary_key=True,
    )
    association_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    feeder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    association_type: Mapped[AssociationType] = mapped_column(
        SAEnum(
            AssociationType,
            name="default_state_association_type",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            length=16,
        ),
        nullable=False,
    )
    from_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_feature_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    default_state = relationship("DefaultState", back_populates="associations")
```

- [ ] **Step 9: Update utility_network exports**

Modify `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`:

```python
from .aoi import AOI
from .default_state import DefaultState, DefaultStateStatus
from .default_state_association import DefaultStateAssociation
from .default_state_feature import DefaultStateFeature
from .feeder import Feeder
from .network_association import AssociationType, NetworkAssociation
from .network_feature import FeatureType, NetworkFeature
from .network_state import NetworkState

__all__ = [
    "AOI",
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
]
```

- [ ] **Step 10: Update Alembic env imports**

In `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`, replace the old utility import block with:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (  # noqa: E402, F401
    AOI,
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
from utility_service.infrastructure.postgresql.models.work_order import (  # noqa: E402, F401
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionOperationState,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
```

- [x] **Step 11: Delete old utility_network work-order models**

Delete:

```text
apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py
apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py
```

- [ ] **Step 12: Run metadata tests**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: PASS for metadata tests after minor import/name fixes. If mapper configuration fails due relationship strings, import all new models in `models/work_order/__init__.py` and `alembic/env.py` exactly as above.

- [ ] **Step 13: Checkpoint**

Do not run `git add` or `git commit`. Record that ORM package boundaries are implemented.

---

### Task 3: Structural Alembic Migration

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b4c6d8e9a1_data_model_boundaries.py`
- Modify: `apps/backend/tests/integration_tests/test_edit_version_migration.py`

- [ ] **Step 1: Rewrite migration integration test constants**

In `apps/backend/tests/integration_tests/test_edit_version_migration.py`, replace constants with:

```python
PREVIOUS_REVISION = "a8c1f2d3e4b5"
DATA_MODEL_BOUNDARIES_REVISION = "f2b4c6d8e9a1"
USER_SCHEMA = "user"
WORK_ORDER_SCHEMA = "work_order"
NETWORK_SCHEMA = "utility_network"
USER_TABLES = {"users"}
WORK_ORDER_TABLES = {
    "work_orders",
    "edit_versions",
    "edit_version_features",
    "edit_version_associations",
}
UTILITY_BASELINE_TABLES = {
    "network_states",
    "default_states",
    "default_state_features",
    "default_state_associations",
}
REMOVED_UTILITY_WORKFLOW_TABLES = {"work_orders", "edit_versions"}
```

- [ ] **Step 2: Add schema/table reader helpers**

Add:

```python
def read_tables(schema_name: str, table_names: set[str]) -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema_name
              AND tablename = ANY(:table_names)
            """,
            {"schema_name": schema_name, "table_names": list(table_names)},
        )
    )


def read_cross_schema_foreign_keys() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT constraint_info.conname
            FROM pg_constraint AS constraint_info
            JOIN pg_class AS source_table
              ON source_table.oid = constraint_info.conrelid
            JOIN pg_namespace AS source_schema
              ON source_schema.oid = source_table.relnamespace
            JOIN pg_class AS target_table
              ON target_table.oid = constraint_info.confrelid
            JOIN pg_namespace AS target_schema
              ON target_schema.oid = target_table.relnamespace
            WHERE constraint_info.contype = 'f'
              AND source_schema.nspname IN ('user', 'utility_network', 'work_order')
              AND target_schema.nspname IN ('user', 'utility_network', 'work_order')
              AND source_schema.nspname <> target_schema.nspname
            """
        )
    )
```

- [ ] **Step 3: Replace schema contract assertion**

Replace `assert_edit_version_schema_contract` with:

```python
def assert_data_model_boundaries_schema_contract() -> None:
    assert read_tables(USER_SCHEMA, USER_TABLES) == USER_TABLES
    assert read_tables(WORK_ORDER_SCHEMA, WORK_ORDER_TABLES) == WORK_ORDER_TABLES
    assert read_tables(NETWORK_SCHEMA, UTILITY_BASELINE_TABLES) == UTILITY_BASELINE_TABLES
    assert read_tables(NETWORK_SCHEMA, REMOVED_UTILITY_WORKFLOW_TABLES) == set()
    assert read_cross_schema_foreign_keys() == set()
```

- [ ] **Step 4: Replace upgrade/downgrade cycle test**

Replace `test_edit_version_migration_upgrade_downgrade_upgrade_cycle` with:

```python
def test_data_model_boundaries_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.upgrade(config, DATA_MODEL_BOUNDARIES_REVISION)
        assert_data_model_boundaries_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert read_tables(WORK_ORDER_SCHEMA, WORK_ORDER_TABLES) == set()
        assert read_tables(USER_SCHEMA, USER_TABLES) == set()

        command.upgrade(config, DATA_MODEL_BOUNDARIES_REVISION)
        assert_data_model_boundaries_schema_contract()
    finally:
        command.upgrade(config, "head")
```

- [ ] **Step 5: Replace duplicate open version SQL**

Replace `OPEN_VERSION_DUPLICATE_SQL` with SQL using new schemas:

```python
OPEN_VERSION_DUPLICATE_SQL = """
WITH demo_user AS (
    INSERT INTO "user".users (id, email, password_hash, role, is_active)
    VALUES (
        '22222222-2222-4222-8222-222222222222',
        'edit-version-concurrency@example.local',
        'hash',
        'editor',
        true
    )
    ON CONFLICT (email) DO UPDATE SET is_active = excluded.is_active
    RETURNING id
),
demo_work_order AS (
    INSERT INTO work_order.work_orders (
        id,
        code,
        title,
        status,
        assignee_user_id
    )
    VALUES (
        '55555555-5555-4555-8555-555555555555',
        'WO-EDIT-VERSION-CONCURRENCY',
        'Проверка уникальности EditVersion',
        'assigned',
        '22222222-2222-4222-8222-222222222222'
    )
    ON CONFLICT (code) DO UPDATE SET status = excluded.status
    RETURNING id
)
INSERT INTO work_order.edit_versions (
    id,
    work_order_id,
    owner_user_id,
    default_state_id,
    base_network_revision,
    status
)
VALUES
    (
        '66666666-6666-4666-8666-666666666661',
        '55555555-5555-4555-8555-555555555555',
        '22222222-2222-4222-8222-222222222222',
        '77777777-7777-4777-8777-777777777777',
        1,
        'open'
    ),
    (
        '66666666-6666-4666-8666-666666666662',
        '55555555-5555-4555-8555-555555555555',
        '22222222-2222-4222-8222-222222222222',
        '77777777-7777-4777-8777-777777777777',
        1,
        'open'
    )
"""
```

- [ ] **Step 6: Update duplicate index test upgrade target**

Use:

```python
command.upgrade(config, DATA_MODEL_BOUNDARIES_REVISION)
```

Expected duplicate error still contains `uq_edit_versions_open_work_order`.

- [ ] **Step 7: Run migration test and verify failure**

Run:

```powershell
cd apps/backend
$env:RUN_DB_TESTS='1'; pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected: FAIL because migration revision `f2b4c6d8e9a1` does not exist.

- [ ] **Step 8: Create reset-style structural migration**

Create `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b4c6d8e9a1_data_model_boundaries.py`:

```python
"""data model boundaries

Revision ID: f2b4c6d8e9a1
Revises: a8c1f2d3e4b5
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2b4c6d8e9a1"
down_revision: Union[str, Sequence[str], None] = "a8c1f2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NETWORK_STATE_ID = "11111111-1111-4111-8111-111111111111"


def upgrade() -> None:
    op.drop_index("uq_edit_versions_open_work_order", table_name="edit_versions", schema="utility_network")
    op.drop_table("edit_versions", schema="utility_network")
    op.drop_index("ix_work_orders_feeder_id", table_name="work_orders", schema="utility_network")
    op.drop_index("ix_work_orders_aoi_id", table_name="work_orders", schema="utility_network")
    op.drop_index("ix_work_orders_status", table_name="work_orders", schema="utility_network")
    op.drop_index("ix_work_orders_assignee_id", table_name="work_orders", schema="utility_network")
    op.drop_table("work_orders", schema="utility_network")
    op.drop_table("default_states", schema="utility_network")
    op.drop_table("users")

    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "user"'))
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS work_order"))

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("password_hash", sa.String(length=1024), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('editor', 'reviewer')", name="user_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="user",
    )

    op.create_table(
        "network_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("current_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("current_revision >= 1", name="ck_network_states_current_revision_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_network_states_name"),
        schema="utility_network",
    )
    op.execute(
        sa.text(
            f"""
            INSERT INTO utility_network.network_states (id, name, current_revision)
            VALUES ('{NETWORK_STATE_ID}', 'default', 1)
            """
        )
    )

```

After the `network_states` insert, the migration must contain concrete `op.create_table`
calls for these tables, in this order:

```text
work_order.work_orders
utility_network.default_states
utility_network.default_state_features
utility_network.default_state_associations
work_order.edit_versions
work_order.edit_version_features
work_order.edit_version_associations
```

Use the exact columns and constraint names from Task 1 metadata tests and Task 2 ORM
models. Do not create cross-schema FK. Internal FK allowed:

```python
sa.ForeignKeyConstraint(
    ["work_order_id"],
    ["work_order.work_orders.id"],
    name="fk_edit_versions_work_order",
    ondelete="RESTRICT",
)
```

For downgrade, drop in reverse order:

```python
def downgrade() -> None:
    op.drop_table("edit_version_associations", schema="work_order")
    op.drop_table("edit_version_features", schema="work_order")
    op.drop_index("uq_edit_versions_open_work_order", table_name="edit_versions", schema="work_order")
    op.drop_table("edit_versions", schema="work_order")
    op.drop_index("ix_work_orders_status", table_name="work_orders", schema="work_order")
    op.drop_index("ix_work_orders_assignee_user_id", table_name="work_orders", schema="work_order")
    op.drop_table("work_orders", schema="work_order")
    op.drop_table("default_state_associations", schema="utility_network")
    op.drop_table("default_state_features", schema="utility_network")
    op.drop_table("default_states", schema="utility_network")
    op.drop_table("network_states", schema="utility_network")
    op.drop_table("users", schema="user")
    op.execute(sa.text('DROP SCHEMA "user"'))
    op.execute(sa.text("DROP SCHEMA work_order"))
```

After dropping the new schemas, recreate the old downgrade shape with concrete
`op.create_table` calls for:

```text
public.users
utility_network.work_orders
utility_network.default_states
utility_network.edit_versions
```

Use the column, FK, check, unique constraint, and index definitions from revisions
`c6cef6320f1d`, `e4b7a9c2d5f8`, and `a8c1f2d3e4b5`.

- [ ] **Step 9: Run migration tests**

Run:

```powershell
cd apps/backend
$env:RUN_DB_TESTS='1'; pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected: PASS.

- [ ] **Step 10: Checkpoint**

Do not run `git add` or `git commit`. Record that structural migration passes.

---

### Task 4: Aggregate Repository And DefaultState Repository

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py`
- Delete: `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`
- Modify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`

- [ ] **Step 1: Update service test fake repository contract**

In `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`, change `build_service` defaults:

```python
work_order_repository=work_order_repository
or repository(
    get_by_id=None,
    get_open_edit_version=None,
    create_open_edit_version=None,
    touch_edit_version=None,
    save=None,
),
default_state_repository=default_state_repository
or repository(get_active_aggregate_by_work_order_id=None),
```

Remove `edit_version_repository` parameter from `build_service` and `EditVersionService(...)`.

- [ ] **Step 2: Update test helpers for new field names**

Change `work_order` helper:

```python
def work_order(
    assignee_id,
    *,
    status: WorkOrderStatus = WorkOrderStatus.ASSIGNED,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        code="WO-001",
        assignee_user_id=assignee_id,
        status=status,
    )
```

Change `default_state` helper:

```python
def default_state(network_revision: int = 12) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), work_order_id=uuid4(), network_revision=network_revision)
```

Change `edit_version` helper:

```python
def edit_version(work_order_id, owner_id, *, base_network_revision: int = 12) -> SimpleNamespace:
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_user_id=owner_id,
        default_state_id=uuid4(),
        base_network_revision=base_network_revision,
        status=EditVersionStatus.OPEN,
        created_at=now,
        last_opened_at=now,
    )
```

- [ ] **Step 3: Update create test expectations**

In `test_open_assigned_work_order_creates_edit_version_and_starts_work_order`, use:

```python
work_order_repository = repository(
    get_by_id=assigned,
    get_open_edit_version=None,
    create_open_edit_version=created,
    touch_edit_version=None,
    save=None,
)
default_state_repository = repository(get_active_aggregate_by_work_order_id=baseline_aggregate)
```

Assert:

```python
default_state_repository.get_active_aggregate_by_work_order_id.assert_awaited_once_with(
    assigned.id
)
work_order_repository.create_open_edit_version.assert_awaited_once_with(
    work_order_id=assigned.id,
    default_state_id=baseline.id,
    base_network_revision=baseline.base_network_revision,
    default_features=baseline_aggregate.features,
    default_associations=baseline_aggregate.associations,
    owner_user_id=actor.id,
)
work_order_repository.save.assert_awaited_once_with(assigned)
```

- [ ] **Step 4: Update existing version tests**

Replace calls to `edit_version_repository.get_open_by_work_order_id` with `work_order_repository.get_open_edit_version`.
Replace `touch_last_opened(existing)` with:

```python
work_order_repository.touch_edit_version.assert_awaited_once_with(existing)
```

- [ ] **Step 5: Run service test and verify failure**

Run:

```powershell
cd apps/backend
pytest utility_service/use_cases/tests/test_edit_version_service.py -q
```

Expected: FAIL because `EditVersionService` still requires `EditVersionRepository`.

- [ ] **Step 6: Implement aggregate repository methods**

`WorkOrderRepository` must not read `DefaultStateFeature` or
`DefaultStateAssociation` itself. It receives baseline rows from
`EditVersionService` and only writes `work_order.*` aggregate tables.

Use imports like:

```python
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
)
```

Implement methods:

```python
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
        owner_user_id=owner_user_id,
        default_state_id=default_state_id,
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
```

Also update existing `list_assigned_to_user` to use `WorkOrder.assignee_user_id`.

- [ ] **Step 7: Implement DefaultStateRepository methods**

Update `default_state_repository.py`:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateAggregate,
    DefaultStateAssociationCopy,
    DefaultStateCopy,
    DefaultStateFeatureCopy,
)


class DefaultStateRepository:
    ...

    async def get_active_aggregate_by_work_order_id(
        self, work_order_id: UUID
    ) -> DefaultStateAggregate | None:
        ...
```

Do not keep `get_default()`, `get_active_by_work_order_id`,
`list_features` or `list_associations` as the service path.

- [ ] **Step 8: Delete EditVersionRepository**

Delete:

```text
apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py
```

- [ ] **Step 9: Run service tests**

Run:

```powershell
cd apps/backend
pytest utility_service/use_cases/tests/test_edit_version_service.py -q
```

Expected: FAIL until Task 5 updates `EditVersionService`; repository methods should import cleanly.

- [ ] **Step 10: Checkpoint**

Do not run `git add` or `git commit`. Record repository boundary changes.

---

### Task 5: Use Cases, Dependency Wiring, And API Schema

**Files:**
- Modify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/work_order_service.py`
- Modify: `apps/backend/utility_service/use_cases/deps.py`
- Modify: `apps/backend/utility_service/use_cases/schemas/edit_version/edit_version_out.py`
- Modify: `apps/backend/utility_service/web_api/api/work_orders.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Update EditVersionService constructor**

In `edit_version_service.py`, remove `EditVersionRepository` import and constructor parameter.
Use:

```python
class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        default_state_repository: DefaultStateRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.default_state_repository = default_state_repository
```

- [ ] **Step 2: Update EditVersionService open path**

Replace repository calls in `open_for_work_order`:

```python
existing = await self.work_order_repository.get_open_edit_version(work_order.id)
```

For `in_progress`:

```python
await self.work_order_repository.touch_edit_version(existing)
return OpenEditVersionResult(created=False, edit_version=existing)
```

For create:

```python
default_state_aggregate = await self.default_state_repository.get_active_aggregate_by_work_order_id(
    work_order.id
)
if default_state_aggregate is None:
    self.raise_context_invalid()

default_state = default_state_aggregate.state
created = await self.work_order_repository.create_open_edit_version(
    work_order_id=work_order.id,
    default_state_id=default_state.id,
    base_network_revision=default_state.base_network_revision,
    default_features=default_state_aggregate.features,
    default_associations=default_state_aggregate.associations,
    owner_user_id=actor.id,
)
work_order.status = WorkOrderStatus.IN_PROGRESS
await self.work_order_repository.save(work_order)
return OpenEditVersionResult(created=True, edit_version=created)
```

The service owns orchestration and status transition; `WorkOrderRepository`
owns persistence of `work_order.*` rows only.

- [ ] **Step 3: Update assignee checks for renamed field**

In `EditVersionService.get_visible_work_order`:

```python
if work_order is None or work_order.assignee_user_id != actor.id:
```

In `WorkOrderService.require_assigned`:

```python
if work_order.assignee_user_id != actor.id:
```

- [ ] **Step 4: Update dependency wiring**

In `deps.py`, remove import of `EditVersionRepository`, and change `get_edit_version_service`:

```python
def get_edit_version_service(
    session: AsyncSession = Depends(get_session),
) -> EditVersionService:
    return EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        DefaultStateRepository(session),
    )
```

- [ ] **Step 5: Update Pydantic response schema**

In `edit_version_out.py`, replace fields:

```python
owner_user_id: UUID = Field(serialization_alias="ownerUserId")
base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
```

Remove `owner_id` and `base_revision`.

- [ ] **Step 6: Update API response mapping**

In `work_orders.py`, map:

```python
edit_version=EditVersionOut(
    id=edit_version.id,
    work_order_id=edit_version.work_order_id,
    owner_user_id=edit_version.owner_user_id,
    status=status_value,
    base_network_revision=edit_version.base_network_revision,
    created_at=edit_version.created_at,
    last_opened_at=edit_version.last_opened_at,
)
```

- [ ] **Step 7: Update web API tests**

In `test_work_orders_api.py`, change helper:

```python
return SimpleNamespace(
    id=uuid4(),
    work_order_id=work_order_id,
    owner_user_id=owner_id,
    status="open",
    base_network_revision=12,
    created_at=now,
    last_opened_at=now,
)
```

Change assertions:

```python
assert response.json()["editVersion"]["ownerUserId"] == str(user_id)
assert response.json()["editVersion"]["baseNetworkRevision"] == 12
assert "ownerId" not in response.json()["editVersion"]
assert "baseRevision" not in response.json()["editVersion"]
```

- [ ] **Step 8: Run use-case and API tests**

Run:

```powershell
cd apps/backend
pytest utility_service/use_cases/tests/test_edit_version_service.py utility_service/use_cases/tests/test_work_order_service.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

- [ ] **Step 9: Checkpoint**

Do not run `git add` or `git commit`. Record service/API contract changes.

---

### Task 6: Seed WorkOrder And DefaultState

**Files:**
- Modify: `apps/backend/seeds/repositories/seed_work_order_repository.py`
- Modify: `apps/backend/seeds/services/seed_work_order_service.py`
- Modify: `apps/backend/seeds/tests/test_seed_work_order_service.py`
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Update SeedWorkOrderRepository imports**

Use:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    NetworkAssociation,
    NetworkFeature,
    NetworkState,
)
from utility_service.infrastructure.postgresql.models.work_order import WorkOrder
```

- [ ] **Step 2: Update create_work_order**

Change fields:

```python
work_order = WorkOrder(
    id=spec.id,
    code=spec.code,
    title=spec.title,
    description=spec.description,
    status=spec.status,
    assignee_user_id=assignee_id,
)
```

Remove `feeder_id` and `aoi_id` from `WorkOrder(...)`.

- [ ] **Step 3: Add DefaultState creation method**

Add to `SeedWorkOrderRepository`:

```python
async def get_default_state_by_work_order_id(self, work_order_id: UUID) -> DefaultState | None:
    result = await self.session.execute(
        select(DefaultState).where(DefaultState.work_order_id == work_order_id)
    )
    return result.scalars().one_or_none()


async def create_default_state_for_work_order(
    self,
    *,
    work_order_id: UUID,
    feeder_id: UUID,
    aoi_id: UUID,
) -> DefaultState:
    network_state_result = await self.session.execute(
        select(NetworkState).where(NetworkState.name == "default")
    )
    network_state = network_state_result.scalars().one()
    default_state = DefaultState(
        work_order_id=work_order_id,
        network_revision=network_state.current_revision,
        source_feeder_id=feeder_id,
        source_aoi_id=aoi_id,
    )
    self.session.add(default_state)
    await self.session.flush()

    await self.session.execute(
        insert(DefaultStateFeature).from_select(
            [
                "default_state_id",
                "feature_id",
                "feeder_id",
                "asset_code",
                "feature_type",
                "geometry",
                "name",
                "description",
                "properties",
                "version",
            ],
            select(
                default_state.id,
                NetworkFeature.id,
                NetworkFeature.feeder_id,
                NetworkFeature.asset_code,
                NetworkFeature.feature_type,
                NetworkFeature.geometry,
                NetworkFeature.name,
                NetworkFeature.description,
                NetworkFeature.properties,
                NetworkFeature.version,
            ).where(NetworkFeature.feeder_id == feeder_id),
        )
    )
    await self.session.execute(
        insert(DefaultStateAssociation).from_select(
            [
                "default_state_id",
                "association_id",
                "feeder_id",
                "association_type",
                "from_feature_id",
                "to_feature_id",
                "version",
            ],
            select(
                default_state.id,
                NetworkAssociation.id,
                NetworkAssociation.feeder_id,
                NetworkAssociation.association_type,
                NetworkAssociation.from_feature_id,
                NetworkAssociation.to_feature_id,
                NetworkAssociation.version,
            ).where(NetworkAssociation.feeder_id == feeder_id),
        )
    )
    await self.session.flush()
    return default_state
```

Also import `insert` from SQLAlchemy.

- [ ] **Step 4: Update seed service flow**

In `SeedWorkOrderService.ensure_work_order`, after existing work order lookup:

```python
if existing is not None:
    existing_default_state = await self.repository.get_default_state_by_work_order_id(existing.id)
    if existing_default_state is None:
        feeder = await self.utility_dataset_repository.get_feeder_by_code(
            SEED_WORK_ORDER_SPEC.feeder_code
        )
        if feeder is None:
            raise SeedWorkOrderDependencyError(
                f"Не найден feeder для seed WorkOrder: {SEED_WORK_ORDER_SPEC.feeder_code}"
            )
        aoi = await self.utility_dataset_repository.get_first_aoi()
        if aoi is None:
            raise SeedWorkOrderDependencyError("Не найден AOI для seed WorkOrder.")
        await self.repository.create_default_state_for_work_order(
            work_order_id=existing.id,
            feeder_id=feeder.id,
            aoi_id=aoi.id,
        )
    return SeedWorkOrderResult(work_order_id=existing.id, created=False)
```

After creating a new work order:

```python
await self.repository.create_default_state_for_work_order(
    work_order_id=work_order.id,
    feeder_id=feeder.id,
    aoi_id=aoi.id,
)
```

- [ ] **Step 5: Update seed unit tests**

In `test_seed_work_order_service.py`, fake repository must include:

```python
get_default_state_by_work_order_id=AsyncMock(return_value=None)
create_default_state_for_work_order=AsyncMock()
```

Add assertion in creation test:

```python
repository.create_default_state_for_work_order.assert_awaited_once_with(
    work_order_id=created_work_order.id,
    feeder_id=feeder.id,
    aoi_id=aoi.id,
)
```

Add test:

```python
def test_existing_work_order_creates_missing_default_state() -> None:
    existing = SimpleNamespace(id=uuid4(), code="WO-001")
    feeder = SimpleNamespace(id=uuid4())
    aoi = SimpleNamespace(id=uuid4())
    repository = repository_fake(
        get_work_order_by_code=existing,
        get_default_state_by_work_order_id=None,
        create_default_state_for_work_order=None,
    )
    service = SeedWorkOrderService(
        FakeSession(),
        repository,
        repository_fake(get_by_email=SimpleNamespace(id=uuid4())),
        repository_fake(get_feeder_by_code=feeder, get_first_aoi=aoi),
    )

    result = asyncio.run(service.ensure_work_order())

    assert result.created is False
    repository.create_default_state_for_work_order.assert_awaited_once_with(
        work_order_id=existing.id,
        feeder_id=feeder.id,
        aoi_id=aoi.id,
    )
```

Use the existing fake helper names in that file; adapt `repository_fake` to the actual local helper name.

- [ ] **Step 6: Run seed tests**

Run:

```powershell
cd apps/backend
pytest seeds/tests/test_seed_work_order_service.py tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: unit tests PASS; integration test may require `RUN_DB_TESTS=1` and database.

- [ ] **Step 7: Checkpoint**

Do not run `git add` or `git commit`. Record seed flow changes.

---

### Task 7: Clean Imports And Architecture Tests

**Files:**
- Modify any backend file importing `models.utility_network.WorkOrder`, `WorkOrderStatus`, `EditVersion`, or `EditVersionStatus`.
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`
- Modify: `apps/backend/tests/test_architecture_boundaries.py` only if it reports a real boundary change.

- [ ] **Step 1: Find old imports**

Run:

```powershell
rg -n "models\\.utility_network import \\(|WorkOrder|EditVersion" apps\\backend\\utility_service apps\\backend\\seeds apps\\backend\\tests
```

Expected: references remain in tests and code. Every import of `WorkOrder`, `WorkOrderStatus`, `EditVersion`, `EditVersionStatus`, `EditVersionFeature`, or `EditVersionAssociation` must come from `models.work_order`.

- [ ] **Step 2: Update common import pattern**

Change:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
```

to:

```python
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
```

- [ ] **Step 3: Verify no old work-order exports**

Run:

```powershell
rg -n "from utility_service\\.infrastructure\\.postgresql\\.models\\.utility_network import \\([\\s\\S]*WorkOrder|from utility_service\\.infrastructure\\.postgresql\\.models\\.utility_network import WorkOrder|EditVersionRepository" apps\\backend
```

Expected: no matches for old work-order model imports and no `EditVersionRepository`.

- [ ] **Step 4: Run architecture tests**

Run:

```powershell
cd apps/backend
pytest tests/test_architecture_boundaries.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Do not run `git add` or `git commit`. Record that imports are clean.

---

### Task 8: Final Verification And CI Parity

**Files:**
- No planned source edits unless verification finds a concrete failure.

- [ ] **Step 1: Run backend unit tests**

Run:

```powershell
cd apps/backend
pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run targeted integration tests with database**

If local PostgreSQL/PostGIS test database is running and `DATABASE_URL` points to it:

```powershell
cd apps/backend
$env:RUN_DB_TESTS='1'
pytest tests/integration_tests/test_network_model_integration.py -q
pytest tests/integration_tests/test_network_model_migration.py -q
pytest tests/integration_tests/test_edit_version_migration.py -q
pytest tests/integration_tests/test_seed_utility_dataset_integration.py -q
pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
pytest tests/integration_tests/test_utility_network_repository_integration.py -q
```

Expected: PASS. If DB is unavailable, record that integration DB tests were not run and use compose verification.

- [ ] **Step 3: Run compose startup**

From repository root:

```powershell
docker compose -f infra/docker-compose.yml up -d --build postgis utility_service
docker compose -f infra/docker-compose.yml ps
```

Expected: `utility_service` becomes healthy. If Docker is unavailable, record the environment limitation.

- [ ] **Step 4: Verify health endpoint in compose**

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T utility_service python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
```

Expected:

```text
health ok
```

- [ ] **Step 5: Clean up compose if started**

Run only if Step 3 started containers:

```powershell
docker compose -f infra/docker-compose.yml down -v
```

Expected: containers and volumes removed.

- [ ] **Step 6: Check worktree status**

Run:

```powershell
git status --short
```

Expected: implementation files are modified/untracked; `.obsidian/*` may still show pre-existing unrelated changes. Do not stage or commit unless user explicitly asks.

---

## Self-Review Checklist

- Spec coverage:
  - `"user".users`: Task 1 metadata, Task 2 model, Task 3 migration.
  - `work_order` aggregate: Task 1 metadata, Task 2 models, Task 4 repository, Task 5 service.
  - `DefaultState` baseline and copy rows: Task 1 metadata, Task 2 models, Task 3 migration, Task 6 seed.
  - No cross-schema FK: Task 1 metadata and Task 3 integration query.
  - Deep copy `EditVersion`: Task 4 repository copy insert and Task 5 service path.
  - `baseNetworkRevision`: Task 5 schema/API tests.
  - No `EditVersionRepository`: Task 4 delete and Task 7 search.
  - Seed-only structural migration: Task 3 migration and Task 6 seed.

- Placeholder scan:
  - План проверен поиском на маркеры незавершенности.
  - Исполняемые шаги не должны оставлять отложенные куски в коде.

- Type consistency:
  - `assignee_user_id` is used in `WorkOrder`, services, repositories, and seed.
  - `owner_user_id` is used in `EditVersion`, API schema, and service output.
  - `base_network_revision` maps to `baseNetworkRevision`.
  - `DefaultState.network_revision` is the source for `EditVersion.base_network_revision`.
