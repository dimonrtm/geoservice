# EditVersion From Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать backend-only создание и повторное открытие `EditVersion` от `DefaultState.current_revision` для назначенного `WorkOrder`.

**Architecture:** Добавляется явная модель `DefaultState` как singleton `name="default"` и модель `EditVersion` как рабочий контейнер без snapshot сети. `EditVersionService` работает только через repositories и `AsyncSession`; сервисы не зависят от других сервисов. Публичный API `POST /api/v1/work-orders/{workOrderId}/edit-versions` создает version атомарно с переходом `WorkOrder.assigned -> in_progress` или возвращает существующую open version.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async ORM, Alembic, PostgreSQL/PostGIS, Pydantic v2, pytest.

---

## Scope Check

План покрывает один backend subsystem: `DefaultState` + `EditVersion` + endpoint открытия version. Workspace API, frontend, snapshot сети, change set, reconcile, post и reviewer workflow не входят в реализацию.

## File Structure

- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py`
  - ORM-модель singleton `DefaultState`.
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py`
  - ORM-модель `EditVersion` и enum `EditVersionStatus`.
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`
  - Экспорт новых моделей и enum.
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
  - Импорт новых моделей для Alembic metadata.
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a8c1f2d3e4b5_edit_versions.py`
  - Миграция `default_states`, `edit_versions`, singleton row и partial unique index.
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py`
  - Чтение `DefaultState(name="default")`.
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`
  - Поиск, создание и сохранение open `EditVersion`.
- Create: `apps/backend/utility_service/use_cases/services/edit_version_service.py`
  - Use-case открытия version. Зависимости только от repositories и `AsyncSession`.
- Modify: `apps/backend/utility_service/use_cases/deps.py`
  - Dependency provider `get_edit_version_service`.
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/__init__.py`
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/edit_version_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/open_edit_version_out.py`
  - Response DTO для API.
- Create: `apps/backend/utility_service/web_api/api/work_orders.py`
  - Router `POST /api/v1/work-orders/{workOrderId}/edit-versions`.
- Modify: `apps/backend/utility_service/web_api/api/exception_handlers.py`
  - Structured handler для `WorkOrderApiError`.
- Modify: `apps/backend/utility_service/web_api/main.py`
  - Подключение `work_orders_router`.
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`
  - Metadata tests для новых моделей.
- Create: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
  - Unit tests для state machine.
- Create: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`
  - API tests для `201`, `200`, auth и service errors.
- Create: `apps/backend/tests/integration_tests/test_edit_version_migration.py`
  - Migration/storage tests для singleton и partial unique index.
- Modify: `.github/workflows/ci.yml`
  - Добавить `test_edit_version_migration.py` в существующий PostgreSQL/PostGIS integration-test блок.

---

### Task 1: ORM Metadata For DefaultState And EditVersion

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`

- [ ] **Step 1: Write failing metadata tests**

Append these tests and imports to `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`.

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    AssociationType,
    DefaultState,
    EditVersion,
    EditVersionStatus,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
    WorkOrder,
    WorkOrderStatus,
)
```

Update `test_utility_network_package_exports_public_contract` expected set:

```python
def test_utility_network_package_exports_public_contract() -> None:
    from utility_service.infrastructure.postgresql.models import utility_network

    assert set(utility_network.__all__) == {
        "AOI",
        "AssociationType",
        "DefaultState",
        "EditVersion",
        "EditVersionStatus",
        "Feeder",
        "FeatureType",
        "NetworkAssociation",
        "NetworkFeature",
        "WorkOrder",
        "WorkOrderStatus",
    }
```

Add tests:

```python
def test_default_state_metadata_contains_singleton_revision_guards() -> None:
    assert DefaultState.__tablename__ == "default_states"
    assert DefaultState.__table__.schema == "utility_network"
    assert {column.name for column in DefaultState.__table__.columns} == {
        "id",
        "name",
        "current_revision",
        "created_at",
        "updated_at",
    }
    assert DefaultState.__table__.c.current_revision.default.arg == 1
    assert str(DefaultState.__table__.c.current_revision.server_default.arg) == "1"
    assert {
        "uq_default_states_name",
        "ck_default_states_current_revision_positive",
    }.issubset(constraint_names(DefaultState))
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("name",)
        for constraint in DefaultState.__table__.constraints
    )


def test_edit_version_status_values_are_stable_strings() -> None:
    assert {item.value for item in EditVersionStatus} == {"open"}


def test_edit_version_metadata_contains_open_version_guards() -> None:
    assert EditVersion.__tablename__ == "edit_versions"
    assert EditVersion.__table__.schema == "utility_network"
    assert {column.name for column in EditVersion.__table__.columns} == {
        "id",
        "work_order_id",
        "owner_id",
        "base_revision",
        "status",
        "created_at",
        "last_opened_at",
    }
    assert EditVersion.__table__.c.base_revision.default.arg == 1
    assert str(EditVersion.__table__.c.base_revision.server_default.arg) == "1"
    assert {
        "ck_edit_versions_base_revision_positive",
        "ck_edit_versions_status",
    }.issubset(constraint_names(EditVersion))


def test_edit_version_foreign_keys_are_restrictive_and_schema_qualified() -> None:
    foreign_keys = [
        constraint
        for constraint in EditVersion.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 2
    assert {element.ondelete for constraint in foreign_keys for element in constraint.elements} == {
        "RESTRICT"
    }
    assert {
        element.target_fullname for constraint in foreign_keys for element in constraint.elements
    } == {
        "users.id",
        "utility_network.work_orders.id",
    }


def test_edit_version_declares_partial_open_unique_index() -> None:
    indexes = {
        index.name: index
        for index in EditVersion.__table__.indexes
    }

    assert "uq_edit_versions_open_work_order" in indexes
    index = indexes["uq_edit_versions_open_work_order"]
    assert tuple(column.name for column in index.columns) == ("work_order_id",)
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == "status = 'open'"
```

Update `test_check_constraints_are_named`:

```python
def test_check_constraints_are_named() -> None:
    checks = [
        constraint
        for model in (AOI, NetworkFeature, NetworkAssociation, WorkOrder, DefaultState, EditVersion)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert checks
    assert all(constraint.name for constraint in checks)
```

- [ ] **Step 2: Run metadata tests and verify they fail**

Run from `apps/backend`:

```powershell
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: FAIL with import errors for `DefaultState`, `EditVersion`, or `EditVersionStatus`.

- [ ] **Step 3: Add DefaultState model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/default_state.py`.

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from utility_service.infrastructure.postgresql.models.base import Base


class DefaultState(Base):
    __tablename__ = "default_states"
    __table_args__ = (
        UniqueConstraint("name", name="uq_default_states_name"),
        CheckConstraint(
            "current_revision >= 1",
            name="ck_default_states_current_revision_positive",
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
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

- [ ] **Step 4: Add EditVersion model**

Create `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/edit_version.py`.

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utility_service.infrastructure.postgresql.models.base import Base

if TYPE_CHECKING:
    from utility_service.infrastructure.postgresql.models.user import User
    from utility_service.infrastructure.postgresql.models.utility_network.work_order import WorkOrder


class EditVersionStatus(str, enum.Enum):
    OPEN = "open"


class EditVersion(Base):
    __tablename__ = "edit_versions"
    __table_args__ = (
        CheckConstraint(
            "base_revision >= 1",
            name="ck_edit_versions_base_revision_positive",
        ),
        CheckConstraint(
            "status IN ('open')",
            name="ck_edit_versions_status",
        ),
        Index(
            "uq_edit_versions_open_work_order",
            "work_order_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "utility_network.work_orders.id",
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_edit_versions_owner",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    base_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
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
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    work_order: Mapped[WorkOrder] = relationship()
    owner: Mapped[User] = relationship()
```

- [ ] **Step 5: Export models and register Alembic metadata**

Modify `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`.

```python
from .aoi import AOI
from .default_state import DefaultState
from .edit_version import EditVersion, EditVersionStatus
from .feeder import Feeder
from .network_association import (
    AssociationType,
    NetworkAssociation,
)
from .network_feature import FeatureType, NetworkFeature
from .work_order import WorkOrder, WorkOrderStatus

__all__ = [
    "AOI",
    "AssociationType",
    "DefaultState",
    "EditVersion",
    "EditVersionStatus",
    "Feeder",
    "FeatureType",
    "NetworkAssociation",
    "NetworkFeature",
    "WorkOrder",
    "WorkOrderStatus",
]
```

Modify import tuple in `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`.

```python
from utility_service.infrastructure.postgresql.models.utility_network import (  # noqa: E402, F401
    AOI,
    AssociationType,
    DefaultState,
    EditVersion,
    EditVersionStatus,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
    WorkOrder,
    WorkOrderStatus,
)
```

- [ ] **Step 6: Run metadata tests and verify they pass**

Run:

```powershell
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: PASS.

- [ ] **Step 7: Record metadata task working tree state**

```powershell
git status --short
```

Expected: only files from Task 1 are changed. Do not stage or commit unless the user explicitly asks.

---

### Task 2: Alembic Migration And Storage Constraints

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a8c1f2d3e4b5_edit_versions.py`
- Create: `apps/backend/tests/integration_tests/test_edit_version_migration.py`

- [ ] **Step 1: Write failing migration integration test**

Create `apps/backend/tests/integration_tests/test_edit_version_migration.py`.

```python
import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.integration_tests.network_db_support import require_db_tests


APP_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_REVISION = "e4b7a9c2d5f8"
EDIT_VERSION_REVISION = "a8c1f2d3e4b5"
NETWORK_SCHEMA = "utility_network"
EDIT_VERSION_TABLES = {"default_states", "edit_versions"}
REQUIRED_CONSTRAINTS = {
    "uq_default_states_name",
    "ck_default_states_current_revision_positive",
    "fk_edit_versions_work_order",
    "fk_edit_versions_owner",
    "ck_edit_versions_base_revision_positive",
    "ck_edit_versions_status",
}
REQUIRED_INDEXES = {"uq_edit_versions_open_work_order"}


def alembic_config() -> Config:
    return Config(str(APP_ROOT / "alembic.ini"))


async def scalar_set(sql: str, params: dict | None = None) -> set[str]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text(sql), params or {})
            return set(result.scalars())
    finally:
        await engine.dispose()


def read_edit_version_tables() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema_name
              AND tablename IN ('default_states', 'edit_versions')
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_constraints() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT conname
            FROM pg_constraint AS constraint_info
            JOIN pg_class AS table_info
              ON table_info.oid = constraint_info.conrelid
            JOIN pg_namespace AS schema_info
              ON schema_info.oid = table_info.relnamespace
            WHERE schema_info.nspname = :schema_name
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_indexes() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = :schema_name
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_default_state_rows() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT name || ':' || current_revision::text
            FROM utility_network.default_states
            """
        )
    )


def assert_edit_version_schema_contract() -> None:
    assert read_edit_version_tables() == EDIT_VERSION_TABLES
    assert REQUIRED_CONSTRAINTS.issubset(read_constraints())
    assert REQUIRED_INDEXES.issubset(read_indexes())
    assert read_default_state_rows() == {"default:1"}


def test_edit_version_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        assert read_edit_version_tables() == set()

        command.upgrade(config, EDIT_VERSION_REVISION)
        assert_edit_version_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert read_edit_version_tables() == set()

        command.upgrade(config, EDIT_VERSION_REVISION)
        assert_edit_version_schema_contract()
    finally:
        command.upgrade(config, "head")
```

- [ ] **Step 2: Run migration test and verify it fails**

Run from `apps/backend`:

```powershell
python -m pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected when `DATABASE_URL` is configured: FAIL because revision `a8c1f2d3e4b5` does not exist. If DB tests are disabled by local environment, mark this command as SKIPPED and run it after DB is available.

- [ ] **Step 3: Add migration**

Create `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a8c1f2d3e4b5_edit_versions.py`.

```python
"""add edit versions

Revision ID: a8c1f2d3e4b5
Revises: e4b7a9c2d5f8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a8c1f2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "e4b7a9c2d5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_STATE_ID = "11111111-1111-4111-8111-111111111111"


def upgrade() -> None:
    op.create_table(
        "default_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("current_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_revision >= 1",
            name="ck_default_states_current_revision_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_default_states_name"),
        schema="utility_network",
    )
    op.execute(
        sa.text(
            """
            INSERT INTO utility_network.default_states (id, name, current_revision)
            VALUES (:id, 'default', 1)
            ON CONFLICT (name) DO NOTHING
            """
        ).bindparams(id=DEFAULT_STATE_ID)
    )
    op.create_table(
        "edit_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                name="edit_version_status",
                native_enum=False,
                create_constraint=False,
                length=16,
            ),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "base_revision >= 1",
            name="ck_edit_versions_base_revision_positive",
        ),
        sa.CheckConstraint(
            "status IN ('open')",
            name="ck_edit_versions_status",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["utility_network.work_orders.id"],
            name="fk_edit_versions_work_order",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_edit_versions_owner",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="utility_network",
    )
    op.create_index(
        "uq_edit_versions_open_work_order",
        "edit_versions",
        ["work_order_id"],
        unique=True,
        schema="utility_network",
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_edit_versions_open_work_order",
        table_name="edit_versions",
        schema="utility_network",
    )
    op.drop_table("edit_versions", schema="utility_network")
    op.drop_table("default_states", schema="utility_network")
```

- [ ] **Step 4: Run migration test**

Run:

```powershell
python -m pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected: PASS when DB tests are enabled, otherwise SKIPPED by `require_db_tests()`.

- [ ] **Step 5: Run Alembic upgrade locally if DB is available**

Run:

```powershell
python -m alembic upgrade head
```

Expected: command exits with code 0 and creates `utility_network.default_states` plus `utility_network.edit_versions`.

- [ ] **Step 6: Record migration task working tree state**

```powershell
git status --short
```

Expected: Task 2 files are present in the working tree. Do not stage or commit unless the user explicitly asks.

---

### Task 3: Repositories And EditVersionService

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`
- Create: `apps/backend/utility_service/use_cases/services/edit_version_service.py`
- Create: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`

- [ ] **Step 1: Write failing service tests**

Create `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`.

```python
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.services.edit_version_service import EditVersionService


def user(role: UserRole = UserRole.EDITOR, *, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), role=role, is_active=is_active)


def work_order(assignee_id, *, status: WorkOrderStatus = WorkOrderStatus.ASSIGNED):
    return SimpleNamespace(
        id=uuid4(),
        code="WO-001",
        assignee_id=assignee_id,
        status=status,
    )


def default_state(current_revision: int = 12) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), name="default", current_revision=current_revision)


def edit_version(work_order_id, owner_id, *, base_revision: int = 12) -> SimpleNamespace:
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_id=owner_id,
        base_revision=base_revision,
        status=EditVersionStatus.OPEN,
        created_at=now,
        last_opened_at=now,
    )


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0
        self.in_transaction = False

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        self.in_transaction = True
        try:
            yield self
        finally:
            self.in_transaction = False


def build_service(
    *,
    session: FakeSession | None = None,
    user_repository: AsyncMock | None = None,
    work_order_repository: AsyncMock | None = None,
    edit_version_repository: AsyncMock | None = None,
    default_state_repository: AsyncMock | None = None,
) -> EditVersionService:
    return EditVersionService(
        session=session or FakeSession(),
        user_repository=user_repository or AsyncMock(),
        work_order_repository=work_order_repository or AsyncMock(),
        edit_version_repository=edit_version_repository or AsyncMock(),
        default_state_repository=default_state_repository or AsyncMock(),
    )


def test_open_assigned_work_order_creates_edit_version_and_starts_work_order() -> None:
    actor = user()
    assigned = work_order(actor.id)
    created = edit_version(assigned.id, actor.id)
    session = FakeSession()
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = assigned
    edit_version_repository = AsyncMock()
    edit_version_repository.get_open_by_work_order_id.return_value = None
    edit_version_repository.create_open.return_value = created
    default_state_repository = AsyncMock()
    default_state_repository.get_default.return_value = default_state(12)
    service = build_service(
        session=session,
        user_repository=user_repository,
        work_order_repository=work_order_repository,
        edit_version_repository=edit_version_repository,
        default_state_repository=default_state_repository,
    )

    result = asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert result.created is True
    assert result.edit_version is created
    assert assigned.status is WorkOrderStatus.IN_PROGRESS
    assert session.begin_calls == 1
    edit_version_repository.create_open.assert_awaited_once_with(
        work_order_id=assigned.id,
        owner_id=actor.id,
        base_revision=12,
    )
    work_order_repository.save.assert_awaited_once_with(assigned)


def test_open_in_progress_work_order_returns_existing_edit_version() -> None:
    actor = user()
    started = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    existing = edit_version(started.id, actor.id)
    edit_version_repository = AsyncMock()
    edit_version_repository.get_open_by_work_order_id.return_value = existing
    service = build_service(
        user_repository=AsyncMock(get_by_id=AsyncMock(return_value=actor)),
        work_order_repository=AsyncMock(get_by_id=AsyncMock(return_value=started)),
        edit_version_repository=edit_version_repository,
        default_state_repository=AsyncMock(),
    )

    result = asyncio.run(service.open_for_work_order(started.id, actor.id))

    assert result.created is False
    assert result.edit_version is existing
    edit_version_repository.touch_last_opened.assert_awaited_once_with(existing)
    edit_version_repository.create_open.assert_not_awaited()


@pytest.mark.parametrize(
    "actor",
    [
        user(UserRole.REVIEWER),
        user(UserRole.EDITOR, is_active=False),
    ],
)
def test_open_rejects_non_active_editor(actor: SimpleNamespace) -> None:
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    work_order_repository = AsyncMock()
    service = build_service(
        user_repository=user_repository,
        work_order_repository=work_order_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(uuid4(), actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    work_order_repository.get_by_id.assert_not_awaited()


def test_open_masks_wrong_assignee_as_not_found() -> None:
    actor = user()
    assigned_to_other = work_order(uuid4())
    service = build_service(
        user_repository=AsyncMock(get_by_id=AsyncMock(return_value=actor)),
        work_order_repository=AsyncMock(get_by_id=AsyncMock(return_value=assigned_to_other)),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned_to_other.id, actor.id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "WORK_ORDER_NOT_FOUND"


def test_open_rejects_missing_default_state() -> None:
    actor = user()
    assigned = work_order(actor.id)
    service = build_service(
        user_repository=AsyncMock(get_by_id=AsyncMock(return_value=actor)),
        work_order_repository=AsyncMock(get_by_id=AsyncMock(return_value=assigned)),
        edit_version_repository=AsyncMock(get_open_by_work_order_id=AsyncMock(return_value=None)),
        default_state_repository=AsyncMock(get_default=AsyncMock(return_value=None)),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"


def test_open_rejects_assigned_work_order_with_existing_open_version() -> None:
    actor = user()
    assigned = work_order(actor.id)
    existing = edit_version(assigned.id, actor.id)
    service = build_service(
        user_repository=AsyncMock(get_by_id=AsyncMock(return_value=actor)),
        work_order_repository=AsyncMock(get_by_id=AsyncMock(return_value=assigned)),
        edit_version_repository=AsyncMock(get_open_by_work_order_id=AsyncMock(return_value=existing)),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"


def test_open_rejects_in_progress_work_order_without_existing_open_version() -> None:
    actor = user()
    started = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    service = build_service(
        user_repository=AsyncMock(get_by_id=AsyncMock(return_value=actor)),
        work_order_repository=AsyncMock(get_by_id=AsyncMock(return_value=started)),
        edit_version_repository=AsyncMock(get_open_by_work_order_id=AsyncMock(return_value=None)),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(started.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"
```

- [ ] **Step 2: Run service tests and verify they fail**

Run:

```powershell
python -m pytest utility_service/use_cases/tests/test_edit_version_service.py -q
```

Expected: FAIL because `edit_version_service.py` does not exist.

- [ ] **Step 3: Add repositories**

Create `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py`.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import DefaultState


class DefaultStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_default(self) -> DefaultState | None:
        result = await self.session.execute(
            select(DefaultState).where(DefaultState.name == "default")
        )
        return result.scalars().one_or_none()
```

Create `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`.

```python
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersion,
    EditVersionStatus,
)


class EditVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_open_by_work_order_id(self, work_order_id: UUID) -> EditVersion | None:
        result = await self.session.execute(
            select(EditVersion).where(
                EditVersion.work_order_id == work_order_id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        return result.scalars().one_or_none()

    async def create_open(
        self,
        *,
        work_order_id: UUID,
        owner_id: UUID,
        base_revision: int,
    ) -> EditVersion:
        edit_version = EditVersion(
            work_order_id=work_order_id,
            owner_id=owner_id,
            base_revision=base_revision,
            status=EditVersionStatus.OPEN,
        )
        self.session.add(edit_version)
        await self.session.flush()
        return edit_version

    async def touch_last_opened(self, edit_version: EditVersion) -> None:
        edit_version.last_opened_at = datetime.now(timezone.utc)
        self.session.add(edit_version)
        await self.session.flush()
```

- [ ] **Step 4: Add EditVersionService**

Create `apps/backend/utility_service/use_cases/services/edit_version_service.py`.

```python
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


@dataclass(frozen=True)
class OpenEditVersionResult:
    created: bool
    edit_version: EditVersion


class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        edit_version_repository: EditVersionRepository,
        default_state_repository: DefaultStateRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.edit_version_repository = edit_version_repository
        self.default_state_repository = default_state_repository

    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            existing = await self.edit_version_repository.get_open_by_work_order_id(work_order.id)

            if work_order.status is WorkOrderStatus.IN_PROGRESS:
                if existing is None:
                    self.raise_context_invalid()
                await self.edit_version_repository.touch_last_opened(existing)
                return OpenEditVersionResult(created=False, edit_version=existing)

            if work_order.status is not WorkOrderStatus.ASSIGNED:
                raise WorkOrderApiError(
                    409,
                    "WORK_ORDER_STATE_CONFLICT",
                    "Состояние рабочей задачи не допускает операцию.",
                )

            if existing is not None:
                self.raise_context_invalid()

            default_state = await self.default_state_repository.get_default()
            if default_state is None:
                self.raise_context_invalid()

            created = await self.edit_version_repository.create_open(
                work_order_id=work_order.id,
                owner_id=actor.id,
                base_revision=default_state.current_revision,
            )
            work_order.status = WorkOrderStatus.IN_PROGRESS
            await self.work_order_repository.save(work_order)
            return OpenEditVersionResult(created=True, edit_version=created)

    async def get_actor(self, actor_id: UUID) -> User:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_ACTOR_NOT_FOUND",
                "Пользователь не найден.",
            )
        self.require_active_editor(actor)
        return actor

    async def get_visible_work_order(self, work_order_id: UUID, actor: User) -> WorkOrder:
        work_order = await self.work_order_repository.get_by_id(work_order_id)
        if work_order is None or work_order.assignee_id != actor.id:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        return work_order

    def require_active_editor(self, actor: User) -> None:
        if actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    def raise_context_invalid(self) -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )
```

- [ ] **Step 5: Run service tests**

Run:

```powershell
python -m pytest utility_service/use_cases/tests/test_edit_version_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Record service task working tree state**

```powershell
git status --short
```

Expected: Task 3 files are present in the working tree. Do not stage or commit unless the user explicitly asks.

---

### Task 4: Work Orders API Endpoint

**Files:**
- Modify: `apps/backend/utility_service/use_cases/deps.py`
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/__init__.py`
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/edit_version_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/edit_version/open_edit_version_out.py`
- Create: `apps/backend/utility_service/web_api/api/work_orders.py`
- Modify: `apps/backend/utility_service/web_api/api/exception_handlers.py`
- Modify: `apps/backend/utility_service/web_api/main.py`
- Create: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Write failing API tests**

Create `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`.

```python
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.infrastructure.postgresql.models.utility_network import EditVersionStatus
from utility_service.use_cases.deps import get_auth_service, get_edit_version_service
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.services.edit_version_service import OpenEditVersionResult
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.work_orders import work_orders_router


def build_app(auth_service: object, edit_version_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(work_orders_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_edit_version_service] = lambda: edit_version_service
    return app


def auth_context(role: str, *, is_active: bool = True):
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email=f"{role}@example.local",
        role=SimpleNamespace(value=role),
        is_active=is_active,
    )
    return auth_service, token, user_id


def edit_version(work_order_id, owner_id):
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_id=owner_id,
        status=EditVersionStatus.OPEN,
        base_revision=12,
        created_at=now,
        last_opened_at=now,
    )


def test_open_edit_version_returns_201_when_created() -> None:
    work_order_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    version = edit_version(work_order_id, user_id)
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.return_value = OpenEditVersionResult(
        created=True,
        edit_version=version,
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["created"] is True
    assert response.json()["editVersion"]["id"] == str(version.id)
    assert response.json()["editVersion"]["workOrderId"] == str(work_order_id)
    assert response.json()["editVersion"]["ownerId"] == str(user_id)
    assert response.json()["editVersion"]["status"] == "open"
    assert response.json()["editVersion"]["baseRevision"] == 12
    edit_version_service.open_for_work_order.assert_awaited_once_with(work_order_id, user_id)


def test_open_edit_version_returns_200_when_reopened() -> None:
    work_order_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    version = edit_version(work_order_id, user_id)
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.return_value = OpenEditVersionResult(
        created=False,
        edit_version=version,
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["created"] is False
    assert response.json()["editVersion"]["id"] == str(version.id)


def test_reviewer_is_denied_before_edit_version_service_call() -> None:
    work_order_id = uuid4()
    auth_service, token, _ = auth_context("reviewer")
    edit_version_service = AsyncMock()

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    edit_version_service.open_for_work_order.assert_not_awaited()


def test_service_error_becomes_structured_response() -> None:
    work_order_id = uuid4()
    auth_service, token, _ = auth_context("editor")
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.side_effect = WorkOrderApiError(
        422,
        "WORK_ORDER_CONTEXT_INVALID",
        "Контекст рабочей задачи поврежден или неполон.",
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "WORK_ORDER_CONTEXT_INVALID"
```

- [ ] **Step 2: Run API tests and verify they fail**

Run:

```powershell
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: FAIL because `get_edit_version_service` and `work_orders.py` do not exist.

- [ ] **Step 3: Add response schemas**

Create `apps/backend/utility_service/use_cases/schemas/edit_version/edit_version_out.py`.

```python
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    work_order_id: UUID = Field(serialization_alias="workOrderId")
    owner_id: UUID = Field(serialization_alias="ownerId")
    status: Literal["open"]
    base_revision: int = Field(serialization_alias="baseRevision")
    created_at: datetime = Field(serialization_alias="createdAt")
    last_opened_at: datetime = Field(serialization_alias="lastOpenedAt")
```

Create `apps/backend/utility_service/use_cases/schemas/edit_version/open_edit_version_out.py`.

```python
from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.edit_version.edit_version_out import EditVersionOut


class OpenEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: bool
    edit_version: EditVersionOut = Field(serialization_alias="editVersion")
```

Create `apps/backend/utility_service/use_cases/schemas/edit_version/__init__.py`.

```python
from utility_service.use_cases.schemas.edit_version.edit_version_out import EditVersionOut
from utility_service.use_cases.schemas.edit_version.open_edit_version_out import OpenEditVersionOut

__all__ = [
    "EditVersionOut",
    "OpenEditVersionOut",
]
```

- [ ] **Step 4: Add dependency provider**

Modify `apps/backend/utility_service/use_cases/deps.py`.

```python
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService
```

Add provider:

```python
def get_edit_version_service(
    session: AsyncSession = Depends(get_session),
) -> EditVersionService:
    return EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        EditVersionRepository(session),
        DefaultStateRepository(session),
    )
```

- [ ] **Step 5: Add Work Orders router**

Create `apps/backend/utility_service/web_api/api/work_orders.py`.

```python
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from utility_service.use_cases.deps import get_edit_version_service
from utility_service.use_cases.schemas.edit_version import EditVersionOut, OpenEditVersionOut
from utility_service.use_cases.services.edit_version_service import EditVersionService
from utility_service.web_api.api.auth import require_editor


work_orders_router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])


@work_orders_router.post(
    "/{work_order_id}/edit-versions",
    response_model=OpenEditVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def open_edit_version(
    work_order_id: UUID,
    response: Response,
    user: Any = Depends(require_editor),
    edit_version_service: EditVersionService = Depends(get_edit_version_service),
) -> OpenEditVersionOut:
    result = await edit_version_service.open_for_work_order(work_order_id, user.id)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    edit_version = result.edit_version
    return OpenEditVersionOut(
        created=result.created,
        edit_version=EditVersionOut(
            id=edit_version.id,
            work_order_id=edit_version.work_order_id,
            owner_id=edit_version.owner_id,
            status=edit_version.status.value,
            base_revision=edit_version.base_revision,
            created_at=edit_version.created_at,
            last_opened_at=edit_version.last_opened_at,
        ),
    )
```

- [ ] **Step 6: Add exception handler and include router**

Modify `apps/backend/utility_service/web_api/api/exception_handlers.py`.

```python
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
```

Add handler inside `install_exception_handlers`:

```python
    @app.exception_handler(WorkOrderApiError)
    async def work_order_api_error(request: Request, error: WorkOrderApiError):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        return JSONResponse(
            status_code=error.status_code,
            content={
                "code": error.code,
                "message": error.message,
                "correlationId": correlation_id,
                "details": {},
            },
        )
```

Modify `apps/backend/utility_service/web_api/main.py`.

```python
from utility_service.web_api.api.work_orders import work_orders_router
```

Include router:

```python
app.include_router(work_orders_router)
```

- [ ] **Step 7: Run API tests**

Run:

```powershell
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

- [ ] **Step 8: Record API task working tree state**

```powershell
git status --short
```

Expected: Task 4 files are present in the working tree. Do not stage or commit unless the user explicitly asks.

---

### Task 5: Storage Concurrency Contract

**Files:**
- Modify: `apps/backend/tests/integration_tests/test_edit_version_migration.py`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add failing storage uniqueness test**

Append to `apps/backend/tests/integration_tests/test_edit_version_migration.py`.

```python
async def open_version_uniqueness_error_sql() -> str:
    return """
    WITH demo_user AS (
        INSERT INTO users (id, email, password_hash, role, is_active)
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
    demo_aoi AS (
        INSERT INTO utility_network.aois (id, name, geometry)
        VALUES (
            '33333333-3333-4333-8333-333333333333',
            'AOI для проверки EditVersion',
            ST_GeomFromText('POLYGON((65.50 44.80,65.54 44.80,65.54 44.84,65.50 44.84,65.50 44.80))', 4326)
        )
        ON CONFLICT (id) DO UPDATE SET name = excluded.name
        RETURNING id
    ),
    demo_feeder AS (
        INSERT INTO utility_network.feeders (id, code, name, is_active)
        VALUES (
            '44444444-4444-4444-8444-444444444444',
            'edit_version_concurrency_feeder',
            'Фидер для проверки EditVersion',
            true
        )
        ON CONFLICT (code) DO UPDATE SET name = excluded.name
        RETURNING id
    ),
    demo_work_order AS (
        INSERT INTO utility_network.work_orders (
            id,
            code,
            title,
            status,
            assignee_id,
            aoi_id,
            feeder_id
        )
        VALUES (
            '55555555-5555-4555-8555-555555555555',
            'WO-EDIT-VERSION-CONCURRENCY',
            'Проверка уникальности EditVersion',
            'assigned',
            '22222222-2222-4222-8222-222222222222',
            '33333333-3333-4333-8333-333333333333',
            '44444444-4444-4444-8444-444444444444'
        )
        ON CONFLICT (code) DO UPDATE SET status = excluded.status
        RETURNING id
    )
    INSERT INTO utility_network.edit_versions (
        id,
        work_order_id,
        owner_id,
        base_revision,
        status
    )
    VALUES
        (
            '66666666-6666-4666-8666-666666666661',
            '55555555-5555-4555-8555-555555555555',
            '22222222-2222-4222-8222-222222222222',
            1,
            'open'
        ),
        (
            '66666666-6666-4666-8666-666666666662',
            '55555555-5555-4555-8555-555555555555',
            '22222222-2222-4222-8222-222222222222',
            1,
            'open'
        )
    """


def test_open_edit_version_partial_unique_index_blocks_duplicates() -> None:
    require_db_tests()
    config = alembic_config()
    command.upgrade(config, EDIT_VERSION_REVISION)

    async def insert_duplicates() -> str:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.begin() as connection:
                try:
                    await connection.execute(text(await open_version_uniqueness_error_sql()))
                except Exception as exc:
                    return str(exc)
                return ""
        finally:
            await engine.dispose()

    message = asyncio.run(insert_duplicates())

    assert "uq_edit_versions_open_work_order" in message
```

- [ ] **Step 2: Run storage uniqueness test**

Run:

```powershell
python -m pytest tests/integration_tests/test_edit_version_migration.py::test_open_edit_version_partial_unique_index_blocks_duplicates -q
```

Expected: PASS when DB tests are enabled, otherwise SKIPPED by `require_db_tests()`.

- [ ] **Step 3: Add edit version migration test to CI**

Modify `.github/workflows/ci.yml` in the existing `PostgreSQL/PostGIS network model tests` step. Add the new command after `test_network_model_migration.py` and before seed integration tests:

```yaml
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_edit_version_migration.py -q
```

The resulting block should include:

```yaml
      - name: PostgreSQL/PostGIS network model tests
        working-directory: infra
        run: |
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_network_model_integration.py -q
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_network_model_migration.py -q
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_edit_version_migration.py -q
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_seed_utility_dataset_integration.py -q
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
          docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_utility_network_repository_integration.py -q
```

- [ ] **Step 4: Record storage contract and CI working tree state**

```powershell
git status --short
```

Expected: Task 5 files and `.github/workflows/ci.yml` are present in the working tree. Do not stage or commit unless the user explicitly asks.

---

### Task 6: Final Verification And Documentation Sync

**Files:**
- Modify if needed: `docs/release_1/sprint_1/README.md`
- Modify if needed: `Code_wiki/архитектура/backend.md`
- Modify if needed: `Code_wiki/архитектура/data_model.md`
- Modify if needed: `Code_wiki/состояние_проекта/repository_change_ingest.md`

- [ ] **Step 1: Run focused backend tests**

Run from `apps/backend`:

```powershell
python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py utility_service/use_cases/tests/test_edit_version_service.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full backend unit suite**

Run:

```powershell
python -m pytest -q
```

Expected: PASS, or existing integration tests SKIPPED when DB is not configured.

- [ ] **Step 3: Run integration migration tests when DB is available**

Run:

```powershell
python -m pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected: PASS when `DATABASE_URL` points to a test Postgres/PostGIS database, otherwise SKIPPED by `require_db_tests()`.

- [ ] **Step 4: Run formatting and lint checks**

Run:

```powershell
python -m ruff check .
python -m black --check .
```

Expected: both commands exit with code 0.

- [ ] **Step 5: Decide repository-change ingest**

If implementation creates durable technical knowledge not already preserved by the design and code, run `/ingest repository-change` via `.agents/skills/source-command-ingest/SKILL.md`. For this task, expected durable knowledge is likely:

```text
EditVersionService opens versions only through repositories.
DefaultState(name="default") anchors base_revision.
Partial unique index protects one open EditVersion per WorkOrder.
```

If the implementation and design documents already preserve this knowledge clearly, record in the final answer that repository-change ingest was not needed.

- [ ] **Step 6: Record final working tree state**

When checks pass and any required docs are updated:

```powershell
git status --short
```

Expected: the output lists the full implementation delta for user review. Do not stage or commit unless the user explicitly asks.

## Self-Review Notes

- Spec coverage: Tasks 1-2 cover `DefaultState`, `EditVersion`, constraints, singleton row and Alembic metadata. Task 3 covers service rules, no service-to-service dependency, strict context invalid behavior and `assigned -> in_progress`. Task 4 covers API response, auth and structured errors. Task 5 covers storage-level duplicate protection and CI inclusion for the new integration test. Task 6 covers verification and repository-change ingest decision.
- Scope control: No task implements workspace API, frontend, snapshot network storage, change set, validation, reconcile, post or reviewer workflow.
- Type consistency: Model names are `DefaultState`, `EditVersion`, `EditVersionStatus`; service entrypoint is `open_for_work_order`; response DTOs are `EditVersionOut` and `OpenEditVersionOut`; API path is `POST /api/v1/work-orders/{workOrderId}/edit-versions`.
