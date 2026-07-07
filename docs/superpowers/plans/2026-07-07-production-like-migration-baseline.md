# Production-Like Migration Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Переписать Alembic chain так, чтобы clean production-like DB создавалась без destructive demo cleanup, а reversible downgrade contract оставался проверяемым в CI.

**Architecture:** Опасные demo/repair ревизии превращаются в compatibility checkpoints, а актуальная схема создается в baseline migrations: `c6` для `user.users`, `d3` для `utility_network`, `e4` для `work_order.aois/work_orders`, `a8` для default/edit-version слоя. Static safety gate запрещает destructive `upgrade()` patterns, DB integration tests проверяют clean upgrade/downgrade cycles, документация фиксирует reset старых local volumes.

**Tech Stack:** Python 3.12, Alembic, SQLAlchemy, GeoAlchemy2, PostgreSQL/PostGIS, pytest, Docker Compose.

---

## File Structure

- Create `apps/backend/tests/test_alembic_upgrade_safety.py`: быстрый static pytest guard для Alembic `upgrade()` functions без живой БД.
- Create `apps/backend/tests/integration_tests/test_user_role_migration.py`: DB migration contract для `user.users` production-like baseline.
- Modify `apps/backend/tests/integration_tests/test_network_model_migration.py`: убрать legacy `utility_network.aois` из expected network schema.
- Modify `apps/backend/tests/integration_tests/test_edit_version_migration.py`: закрепить, что `work_order.aois` и `work_orders.aoi_id` существуют уже на `e4`, а old stamped repair test удален.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c6cef6320f1d_create_users.py`: создать целевые роли `editor/reviewer` и `is_active` сразу.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py`: сделать compatibility checkpoint без data changes.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/d3a01f4e9c21_network_model.py`: убрать legacy `utility_network.aois`.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/e4b7a9c2d5f8_work_orders.py`: создать `work_order.aois`, `aoi_id`, FK и index в baseline.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py`: сделать compatibility checkpoint без table cleanup.
- Modify `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c9d0e1f2a3b4_repair_work_order_aoi_scope.py`: сделать compatibility checkpoint без fallback AOI.
- Modify `README.md`: предупредить о reset старых disposable volumes перед production-like baseline.
- Modify `Code_wiki/dev_setup/local_development.md`: синхронизировать local reset и seed ownership.
- Modify `Code_wiki/архитектура/data_model.md`: обновить описание миграций и seed слоя.
- Modify `Code_wiki/deployment/docker_compose.md`: уточнить clean DB expectation для production-safe baseline.
- Modify `Code_wiki/сборка/ci_and_quality.md`: обновить описание migration-cycle gates.

## Task 1: Static Safety Gate For Alembic Upgrade

**Files:**
- Create: `apps/backend/tests/test_alembic_upgrade_safety.py`

- [ ] **Step 1: Write the failing static safety test**

Create `apps/backend/tests/test_alembic_upgrade_safety.py` with this exact content:

```python
from __future__ import annotations

import ast
import re
from pathlib import Path


ALEMBIC_VERSION_DIR = (
    Path(__file__).resolve().parents[1]
    / "utility_service"
    / "infrastructure"
    / "postgresql"
    / "alembic"
    / "versions"
)

FORBIDDEN_UPGRADE_SQL = {
    "DELETE FROM": re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
    "TRUNCATE": re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    "DROP TABLE": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    "DROP SCHEMA": re.compile(r"\bDROP\s+SCHEMA\b", re.IGNORECASE),
    "ALTER TABLE SET SCHEMA": re.compile(
        r"\bALTER\s+TABLE\b[\s\S]*?\bSET\s+SCHEMA\b",
        re.IGNORECASE,
    ),
}

FORBIDDEN_UPGRADE_OP_CALLS = {"drop_table"}


def upgrade_function(tree: ast.Module) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return node
    raise AssertionError("Migration file has no upgrade() function.")


def iter_string_literals(node: ast.AST):
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value


def iter_forbidden_op_calls(node: ast.AST):
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if not isinstance(child.func, ast.Attribute):
            continue
        if not isinstance(child.func.value, ast.Name):
            continue
        if child.func.value.id != "op":
            continue
        if child.func.attr in FORBIDDEN_UPGRADE_OP_CALLS:
            yield child.func.attr


def test_upgrade_migrations_do_not_run_destructive_data_or_table_cleanup() -> None:
    violations: list[str] = []

    for migration_path in sorted(ALEMBIC_VERSION_DIR.glob("*.py")):
        tree = ast.parse(migration_path.read_text(encoding="utf-8"))
        upgrade = upgrade_function(tree)

        for call_name in iter_forbidden_op_calls(upgrade):
            violations.append(f"{migration_path.name}: upgrade() calls op.{call_name}()")

        for sql_literal in iter_string_literals(upgrade):
            for label, pattern in FORBIDDEN_UPGRADE_SQL.items():
                if pattern.search(sql_literal):
                    violations.append(
                        f"{migration_path.name}: upgrade() contains forbidden SQL {label}"
                    )

    assert violations == []
```

- [ ] **Step 2: Run the safety test to verify it fails**

Run:

```powershell
cd apps/backend
pytest tests/test_alembic_upgrade_safety.py -q
```

Expected: FAIL. The failure list must include at least:

```text
b82a5f2d91c3_editor_reviewer_roles.py: upgrade() contains forbidden SQL DELETE FROM
f2b3c4d5e6a7_sprint1_schema_boundaries.py: upgrade() contains forbidden SQL DROP TABLE
c9d0e1f2a3b4_repair_work_order_aoi_scope.py: upgrade() contains forbidden SQL DROP TABLE
```

## Task 2: Convert Destructive Revisions Into Compatibility Checkpoints

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/f2b3c4d5e6a7_sprint1_schema_boundaries.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c9d0e1f2a3b4_repair_work_order_aoi_scope.py`
- Test: `apps/backend/tests/test_alembic_upgrade_safety.py`

- [ ] **Step 1: Replace `b82a5f2d91c3_editor_reviewer_roles.py`**

Replace the whole file with:

```python
"""compatibility checkpoint for editor/reviewer roles

Revision ID: b82a5f2d91c3
Revises: c6cef6320f1d

The clean production-like baseline now creates user.users with the target
editor/reviewer role set and is_active in c6cef6320f1d. This revision remains
in the Alembic graph so existing revision order is stable, but it must not
delete users or rewrite role constraints during upgrade.
"""

from typing import Sequence, Union


revision: str = "b82a5f2d91c3"
down_revision: Union[str, Sequence[str], None] = "c6cef6320f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 2: Replace `f2b3c4d5e6a7_sprint1_schema_boundaries.py`**

Replace the whole file with:

```python
"""compatibility checkpoint for sprint1 schema boundaries

Revision ID: f2b3c4d5e6a7
Revises: a8c1f2d3e4b5

The clean production-like baseline creates work_order AOI/work-order tables in
e4b7a9c2d5f8 and edit/default-state tables in a8c1f2d3e4b5. Old dev/demo
volumes are intentionally unsupported, so this revision no longer performs
legacy table cleanup or schema repair.
"""

from typing import Sequence, Union


revision: str = "f2b3c4d5e6a7"
down_revision: Union[str, Sequence[str], None] = "a8c1f2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 3: Replace `c9d0e1f2a3b4_repair_work_order_aoi_scope.py`**

Replace the whole file with:

```python
"""compatibility checkpoint for work-order AOI scope repair

Revision ID: c9d0e1f2a3b4
Revises: f2b3c4d5e6a7

The clean production-like baseline creates work_order.aois and
work_order.work_orders.aoi_id in e4b7a9c2d5f8. Old stamped dev volumes are not a
supported migration path, so this revision no longer creates fallback AOI rows
or drops legacy utility_network.aois.
"""

from typing import Sequence, Union


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 4: Run the safety test to verify it passes**

Run:

```powershell
cd apps/backend
pytest tests/test_alembic_upgrade_safety.py -q
```

Expected: PASS.

## Task 3: Add Failing Clean-Baseline Migration Contracts

**Files:**
- Create: `apps/backend/tests/integration_tests/test_user_role_migration.py`
- Modify: `apps/backend/tests/integration_tests/test_network_model_migration.py`
- Modify: `apps/backend/tests/integration_tests/test_edit_version_migration.py`

- [ ] **Step 1: Add user role migration contract**

Create `apps/backend/tests/integration_tests/test_user_role_migration.py` with this exact content:

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
PREVIOUS_REVISION = "7f4dbcd151ee"
USER_ROLE_REVISION = "b82a5f2d91c3"
USER_SCHEMA = "user"


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


async def row_mapping(sql: str, params: dict | None = None) -> dict[str, tuple[str, str]]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text(sql), params or {})
            return {
                row.column_name: (row.is_nullable, row.column_default or "")
                for row in result
            }
    finally:
        await engine.dispose()


def schema_exists(schema_name: str) -> bool:
    return (
        asyncio.run(
            scalar_set(
                """
                SELECT nspname
                FROM pg_namespace
                WHERE nspname = :schema_name
                """,
                {"schema_name": schema_name},
            )
        )
        == {schema_name}
    )


def read_user_columns() -> dict[str, tuple[str, str]]:
    return asyncio.run(
        row_mapping(
            """
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'user'
              AND table_name = 'users'
              AND column_name IN ('id', 'email', 'password_hash', 'role', 'is_active')
            """,
        )
    )


def read_user_constraints() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT pg_get_constraintdef(constraint_info.oid)
            FROM pg_constraint AS constraint_info
            JOIN pg_class AS table_info
              ON table_info.oid = constraint_info.conrelid
            JOIN pg_namespace AS schema_info
              ON schema_info.oid = table_info.relnamespace
            WHERE schema_info.nspname = 'user'
              AND table_info.relname = 'users'
            """,
        )
    )


def test_user_role_migration_creates_production_like_role_baseline() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists(USER_SCHEMA) is False

        command.upgrade(config, USER_ROLE_REVISION)

        columns = read_user_columns()
        assert set(columns) == {"id", "email", "password_hash", "role", "is_active"}
        assert columns["role"][0] == "NO"
        assert columns["is_active"][0] == "NO"
        assert "true" in columns["is_active"][1].lower()

        constraint_text = "\n".join(read_user_constraints()).lower()
        assert "editor" in constraint_text
        assert "reviewer" in constraint_text
        assert "viewer" not in constraint_text
    finally:
        command.upgrade(config, "head")
```

- [ ] **Step 2: Update network migration contract to remove legacy AOI**

In `apps/backend/tests/integration_tests/test_network_model_migration.py`, make these exact replacements:

```python
NETWORK_TABLES = {
    "feeders",
    "network_features",
    "network_associations",
}
```

```python
REQUIRED_INDEXES = {
    "ix_network_features_geometry",
}
EXPECTED_SPATIAL_INDEXES = {
    ("network_features", "geometry"): "ix_network_features_geometry",
}
```

Keep `read_network_tables()` and `read_geometry_gist_indexes()` structurally the same; the updated expected sets make `utility_network.aois` forbidden because any remaining AOI table or GIST index will appear as unexpected data in the assertions.

- [ ] **Step 3: Update edit-version migration contract for AOI baseline**

In `apps/backend/tests/integration_tests/test_edit_version_migration.py`, remove:

```python
SCHEMA_BOUNDARY_REVISION = "f2b3c4d5e6a7"
```

Add this constant near `WORK_ORDER_TABLES`:

```python
WORK_ORDER_BASELINE_TABLES = {"aois", "work_orders"}
```

Replace `assert_edit_version_schema_absent()` with:

```python
def assert_edit_version_schema_absent() -> None:
    assert read_tables(NETWORK_SCHEMA, UTILITY_BASELINE_TABLES) == set()
    assert read_tables(WORK_ORDER_SCHEMA, EDIT_VERSION_TABLES) == set()
    assert read_tables(WORK_ORDER_SCHEMA, WORK_ORDER_BASELINE_TABLES) == WORK_ORDER_BASELINE_TABLES
    assert column_exists(WORK_ORDER_SCHEMA, "work_orders", "aoi_id") is True
    assert utility_network_aoi_exists() is False
```

Delete the whole `test_schema_repair_migration_handles_stamped_boundary_without_aoi_id()` function.

- [ ] **Step 4: Run targeted DB tests to verify they fail for the right reason**

Use a disposable local DB or CI DB with `RUN_DB_TESTS=1`. From inside `apps/backend` with a reachable `DATABASE_URL`, run:

```powershell
$env:RUN_DB_TESTS="1"
pytest tests/integration_tests/test_user_role_migration.py -q
pytest tests/integration_tests/test_network_model_migration.py -q
pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected before Task 4 implementation:

```text
test_user_role_migration.py fails because c6 still creates viewer role and no is_active.
test_network_model_migration.py fails because d3 still creates utility_network.aois.
test_edit_version_migration.py fails because e4 does not create work_order.aois/aoi_id.
```

Proceed directly to Task 4 with these intentionally red tests.

## Task 4: Rewrite Clean Baseline Migrations

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c6cef6320f1d_create_users.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/d3a01f4e9c21_network_model.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/e4b7a9c2d5f8_work_orders.py`
- Test: `apps/backend/tests/test_alembic_upgrade_safety.py`
- Test: `apps/backend/tests/integration_tests/test_user_role_migration.py`
- Test: `apps/backend/tests/integration_tests/test_network_model_migration.py`
- Test: `apps/backend/tests/integration_tests/test_edit_version_migration.py`

- [ ] **Step 1: Update `c6cef6320f1d_create_users.py` role baseline**

In `op.create_table("users", ...)`, replace the `role` column enum values with:

```python
        sa.Column(
            "role",
            sa.Enum(
                "editor",
                "reviewer",
                name="user_role",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
```

Immediately after the `role` column, add:

```python
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
```

- [ ] **Step 2: Remove legacy AOI from `d3a01f4e9c21_network_model.py`**

In `upgrade()`, delete the complete `op.create_table("aois", ...)` block and the following `op.create_index("ix_aois_geometry", ...)` block.

After the change, the start of `upgrade()` must be:

```python
def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA utility_network"))

    op.create_table(
        "feeders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
```

In `downgrade()`, remove these two lines:

```python
    op.execute(sa.text("DROP INDEX IF EXISTS utility_network.ix_aois_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.aois"))
```

The final `downgrade()` order must be:

```python
def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.network_associations"))
    op.execute(sa.text("DROP INDEX IF EXISTS utility_network.ix_network_features_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.network_features"))
    op.execute(sa.text("DROP TABLE IF EXISTS utility_network.feeders"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS utility_network"))
```

- [ ] **Step 3: Add work-order AOI baseline to `e4b7a9c2d5f8_work_orders.py`**

Add this import:

```python
import geoalchemy2
```

Inside `upgrade()`, immediately after `op.execute(sa.text("CREATE SCHEMA work_order"))`, add:

```python
    op.create_table(
        "aois",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
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
            "NOT ST_IsEmpty(geometry)",
            name="ck_aois_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_aois_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_aois_geometry_srid",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')",
            name="ck_aois_geometry_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="work_order",
    )
    op.create_index(
        "ix_aois_geometry",
        "aois",
        ["geometry"],
        unique=False,
        schema="work_order",
        postgresql_using="gist",
    )
```

In the `work_orders` table definition, add `aoi_id` after `status` and before `assignee_user_id`:

```python
        sa.Column("aoi_id", postgresql.UUID(as_uuid=True), nullable=False),
```

In the same `op.create_table("work_orders", ...)`, add this FK before `sa.PrimaryKeyConstraint("id")`:

```python
        sa.ForeignKeyConstraint(
            ["aoi_id"],
            ["work_order.aois.id"],
            name="fk_work_orders_aoi",
            ondelete="RESTRICT",
        ),
```

After the existing `ix_work_orders_assignee_user_id` index, add:

```python
    op.create_index(
        "ix_work_orders_aoi_id",
        "work_orders",
        ["aoi_id"],
        unique=False,
        schema="work_order",
    )
```

Replace `downgrade()` with:

```python
def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_created_by_user_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_aoi_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_work_orders_assignee_user_id"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.work_orders"))
    op.execute(sa.text("DROP INDEX IF EXISTS work_order.ix_aois_geometry"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_order.aois"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS work_order"))
```

- [ ] **Step 4: Run static and unit checks**

Run:

```powershell
cd apps/backend
pytest tests/test_alembic_upgrade_safety.py utility_service/infrastructure/tests/test_user_role_model.py -q
```

Expected: PASS.

- [ ] **Step 5: Run targeted DB migration checks**

Use a disposable local DB or CI DB with `RUN_DB_TESTS=1`. From inside `apps/backend`, run:

```powershell
$env:RUN_DB_TESTS="1"
pytest tests/integration_tests/test_user_role_migration.py -q
pytest tests/integration_tests/test_network_model_migration.py -q
pytest tests/integration_tests/test_edit_version_migration.py -q
```

Expected: all three commands PASS.

- [ ] **Step 6: Run seed integration checks**

Run:

```powershell
cd apps/backend
$env:RUN_DB_TESTS="1"
pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: PASS. This confirms demo AOI still comes from `SeedWorkOrderService`, not from schema migrations.

## Task 5: Update Documentation And Wiki

**Files:**
- Modify: `README.md`
- Modify: `Code_wiki/dev_setup/local_development.md`
- Modify: `Code_wiki/архитектура/data_model.md`
- Modify: `Code_wiki/deployment/docker_compose.md`
- Modify: `Code_wiki/сборка/ci_and_quality.md`

- [ ] **Step 1: Update README local volume guidance**

In `README.md`, after the demo compose command block in “Demo login через Docker Compose”, add:

````markdown
Перед первым запуском ветки с production-like migration baseline пересоздайте
старый disposable Postgres volume. Старые demo/dev volumes с уже примененными
Alembic revisions не являются поддерживаемым migration path:

```bash
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

После этого запустите demo/dev compose снова. Команда удаляет локальные данные
Postgres и предназначена только для disposable demo/dev БД.
````

- [ ] **Step 2: Update local development runbook**

In `Code_wiki/dev_setup/local_development.md`, replace the paragraph that says `seed_utility_dataset` creates `1 AOI, 19 features и 9 associations` with:

```markdown
`python -m seeds.runners.seed_utility_dataset` создаёт
`synthetic_utility_feeder_01`: 19 features и 9 associations. Повторный запуск
при существующем feeder является no-op и сохраняет ручные изменения. AOI больше
не принадлежит utility dataset seed.

`python -m seeds.runners.seed_work_orders` создаёт create-once `WO-001` после
demo users и utility dataset, гарантирует `work_order.AOI` для рабочей области
и активный per-WorkOrder `DefaultState`, скопированный из текущего
`synthetic_utility_feeder_01`.
```

In the same file, after the demo compose command, add:

```markdown
После перехода на production-like migration baseline старые disposable dev/demo
volumes нужно пересоздать. Новая Alembic chain рассчитана на clean DB; old
stamped volumes с промежуточной demo-схемой не чинятся автоматически.
```

- [ ] **Step 3: Update data model migration bullets**

In `Code_wiki/архитектура/data_model.md`, update the “Миграции И Seed” bullets so these revisions read:

```markdown
- `c6cef6320f1d_create_users.py` создаёт схему `user` и таблицу
  `user.users` сразу в production-like виде: роли `editor`/`reviewer`,
  `password_hash`, `created_at` и `is_active`.
- `b82a5f2d91c3_editor_reviewer_roles.py` является compatibility checkpoint:
  модель ролей уже задана в `c6cef6320f1d`, поэтому ревизия не удаляет данные.
- `d3a01f4e9c21_network_model.py` создаёт utility schema, feeder graph,
  geometry/FK/check constraints и spatial index для `network_features`.
  `utility_network.aois` больше не создаётся.
- `e4b7a9c2d5f8_work_orders.py` создаёт `work_order.aois` и
  `work_order.work_orders` с обязательным `aoi_id`, `fk_work_orders_aoi`,
  индексами assignment/status/AOI и plain UUID полями
  `assignee_user_id`/`created_by_user_id` без FK на `user.users`.
- `a8c1f2d3e4b5_edit_versions.py` добавляет `utility_network.network_states`,
  per-WorkOrder `utility_network.default_states`, `default_state_features`,
  `default_state_associations`, а также `work_order.edit_versions`,
  `edit_version_features` и `edit_version_associations`.
- `f2b3c4d5e6a7_sprint1_schema_boundaries.py` является compatibility
  checkpoint. Актуальные schema-boundary объекты уже создаются в baseline
  migrations, поэтому ревизия не выполняет cleanup старых volumes.
- `c9d0e1f2a3b4_repair_work_order_aoi_scope.py` является compatibility
  checkpoint. Old stamped dev volumes не поддерживаются как migration path, а
  demo AOI создаётся через `SeedWorkOrderService`.
```

- [ ] **Step 4: Update docker compose runbook**

In `Code_wiki/deployment/docker_compose.md`, add this paragraph to the Compose Services section:

```markdown
Production-like baseline предполагает clean PostgreSQL/PostGIS DB перед первым
`alembic upgrade head`. Старые локальные `geo_pgdata`/`infra_geo_pgdata`
volumes, созданные до переписывания destructive demo migrations, являются
disposable dev state и пересоздаются через demo/dev `down -v`; production-safe
startup не выполняет автоматический repair таких volumes.
```

- [ ] **Step 5: Update CI quality runbook**

In `Code_wiki/сборка/ci_and_quality.md`, replace the sentence that says migration cycle deletes utility schema data and CI reseeds because of that with:

```markdown
Migration-cycle tests проверяют clean production-like Alembic chain:
`upgrade -> downgrade -> upgrade` для user role, utility network и edit-version
слоёв. Они больше не проверяют repair старых stamped volumes и не ожидают
legacy `utility_network.aois`. Demo seed chain проверяется отдельными seed и
authenticated API smoke gates.
```

- [ ] **Step 6: Run wiki lint**

Run from repository root:

```powershell
python scripts/lint-wiki.py --root .
```

Expected: PASS or existing unrelated warnings only. If the command reports a new broken wiki link from this task, fix the edited wiki link and rerun.

## Task 6: Final Verification And Knowledge Hygiene

**Files:**
- Read: `docs/superpowers/specs/2026-07-07-production-like-migration-baseline-design.md`
- Read: `docs/superpowers/plans/2026-07-07-production-like-migration-baseline.md`
- Read: `git status --short`

- [ ] **Step 1: Run backend static and unit tests**

Run:

```powershell
cd apps/backend
pytest tests/test_alembic_upgrade_safety.py `
  tests/test_compose_startup_contract.py `
  tests/test_compose_security_contract.py `
  utility_service/infrastructure/tests/test_user_role_model.py `
  utility_service/infrastructure/tests/test_network_model_metadata.py `
  seeds/tests/test_seed_work_order_service.py `
  seeds/tests/test_seed_utility_dataset_service.py `
  seeds/tests/test_seed_demo_user_service.py -q
```

Expected: PASS.

- [ ] **Step 2: Run targeted DB integration tests**

Use a clean disposable DB. If using the local demo compose volume and it may contain old stamped state, ask for approval before running a volume reset. Then run:

```powershell
cd apps/backend
$env:RUN_DB_TESTS="1"
pytest tests/integration_tests/test_user_role_migration.py `
  tests/integration_tests/test_network_model_migration.py `
  tests/integration_tests/test_edit_version_migration.py `
  tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full backend unit suite**

Run:

```powershell
cd apps/backend
pytest -q
```

Expected: PASS. DB integration tests without `RUN_DB_TESTS=1` should skip where designed.

- [ ] **Step 4: Run wiki lint**

Run:

```powershell
python scripts/lint-wiki.py --root .
```

Expected: PASS or existing unrelated warnings only.

- [ ] **Step 5: Decide repository-change ingest**

Check whether the implementation revealed durable technical knowledge not already captured by the updated `Code_wiki` nodes. If the answer is no, do not invoke `/ingest repository-change`. If the answer is yes, run `/ingest repository-change` through `.agents/skills/source-command-ingest/SKILL.md` after the code/docs work is complete.

- [ ] **Step 6: Check final git status**

Run:

```powershell
git status --short
```

Expected: only intentional changes remain. Mention any remaining untracked or unstaged files explicitly in the final report.
