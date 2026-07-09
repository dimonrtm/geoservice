# Workspace Aggregate Raw SQL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `WorkOrderRepository.get_workspace_aggregate()` SQLAlchemy expression-builder query with one raw SQL aggregate query that materializes workspace features once and preserves the current Workspace API response contract.

**Architecture:** Add `workspace_aggregate.sql` next to the existing `default_state_aggregate.sql` and expose it through a module-level typed SQLAlchemy `text(...).columns(...)` statement. `WorkOrderRepository` keeps the same public method and returns the existing aggregate shape, but maps scalar raw SQL rows into focused dataclasses instead of depending on ORM entity rows. Authorization, assignee checks, status checks, DTO validation, frontend flow, and public API stay in the current `WorkspaceService` path.

**Tech Stack:** Python 3.12, async SQLAlchemy, PostgreSQL/PostGIS, JSONB, GeoAlchemy2 model metadata, pytest, Docker image `utility_service:dev`.

---

## Current Scope And Preconditions

This plan assumes the current worktree already contains the index hardening that was verified before the plan was written:

- `ix_edit_version_features_geometry` on `work_order.edit_version_features.geometry`
- `ix_edit_version_associations_edit_version_to_feature_id` on `work_order.edit_version_associations(edit_version_id, to_feature_id)`
- metadata and migration tests asserting those indexes and the absence of duplicate target index groups

Do not add another index with the same columns. Keep the existing index changes in the working tree and build the raw SQL refactor on top of them.

The public endpoint remains:

```text
GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace
```

The endpoint must still return one full workspace aggregate in one DB round trip. Do not add paging, bbox API, vector tiles, frontend changes, or a benchmark harness in this plan.

## File Structure

- Create: `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql`
  - Owns only the PostgreSQL/PostGIS aggregate query.
  - Uses `workspace_context`, `workspace_features AS MATERIALIZED`, `features_json`, and `associations_json`.
  - Returns scalar work order/edit version/AOI columns plus `features_data` and `associations_data` JSONB arrays.

- Create: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py`
  - Unit tests for the raw SQL file contract and repository one-round-trip mapping.
  - Uses a fake async session, matching the existing `test_default_state_repository.py` pattern.

- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
  - Add `WORKSPACE_AGGREGATE_SQL_PATH` and `WORKSPACE_AGGREGATE_SQL`.
  - Add `WorkspaceWorkOrderRow` and `WorkspaceEditVersionRow` dataclasses.
  - Replace the expression-builder body of `get_workspace_aggregate()` with one raw SQL execute call and mapping conversion.

- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
  - Add regression coverage that an association is excluded when one endpoint feature is outside AOI.
  - Keep the existing 19 features / 9 associations seeded workspace assertion.

- Modify after code is stable: `Code_wiki/архитектура/data_model.md`, `Code_wiki/правила_и_стиль/testing_strategy.md`, `Code_wiki/сборка/ci_and_quality.md`, `Code_wiki/состояние_проекта/repository_change_ingest.md`, and `Code_wiki/index.md`
  - Reflect durable knowledge: workspace aggregate now lives in `sql/workspace_aggregate.sql` and uses a materialized CTE for AOI membership.

### Task 1: Add Repository Unit Tests For Raw SQL Contract

**Files:**
- Create: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py`
- Read for pattern: `apps/backend/utility_service/infrastructure/tests/test_default_state_repository.py`

- [ ] **Step 1: Create the failing unit test file**

Create `apps/backend/utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py` with this content:

```python
import asyncio
from uuid import uuid4

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WORKSPACE_AGGREGATE_SQL,
    WORKSPACE_AGGREGATE_SQL_PATH,
    WorkOrderRepository,
)


class FakeMappingResult:
    def __init__(self, row):
        self.row = row

    def one_or_none(self):
        return self.row


class FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return FakeMappingResult(self.row)


class FakeSession:
    def __init__(self, row):
        self.row = row
        self.execute_calls = []
        self.scalars_calls = []

    async def execute(self, statement, params):
        self.execute_calls.append((statement, params))
        return FakeResult(self.row)

    async def scalars(self, *args, **kwargs):
        self.scalars_calls.append((args, kwargs))
        raise AssertionError("Workspace aggregate read must use one execute call")


def test_workspace_aggregate_sql_lives_in_sql_file() -> None:
    assert WORKSPACE_AGGREGATE_SQL_PATH.name == "workspace_aggregate.sql"
    sql_text = WORKSPACE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")
    assert "workspace_features AS MATERIALIZED" in sql_text
    assert "JOIN workspace_features AS from_feature" in sql_text
    assert "JOIN workspace_features AS to_feature" in sql_text
    assert "ST_Intersects(context.aoi_geometry, feature.geometry)" in sql_text


def test_get_workspace_aggregate_uses_one_sql_round_trip_and_maps_row() -> None:
    work_order_id = uuid4()
    edit_version_id = uuid4()
    aoi_id = uuid4()
    assignee_user_id = uuid4()
    feature_id = uuid4()
    connected_feature_id = uuid4()
    association_id = uuid4()
    session = FakeSession(
        {
            "work_order_id": work_order_id,
            "work_order_code": "WO-001",
            "work_order_title": "Проверка участка фидера",
            "work_order_description": None,
            "work_order_status": "in_progress",
            "work_order_assignee_user_id": assignee_user_id,
            "edit_version_id": edit_version_id,
            "edit_version_status": "open",
            "edit_version_base_network_revision": 12,
            "aoi_id": aoi_id,
            "aoi_name": "Рабочая область WO-001",
            "aoi_description": None,
            "aoi_geometry_data": {"type": "Polygon", "coordinates": []},
            "aoi_extent": [65.495, 44.795, 65.545, 44.835],
            "features_data": [
                {
                    "id": str(feature_id),
                    "asset_code": "J-001",
                    "feature_type": "junction",
                    "geometry_data": {"type": "Point", "coordinates": [65.5, 44.82]},
                    "properties": {"name": "Junction"},
                    "network_version": 1,
                    "operation": "unchanged",
                }
            ],
            "associations_data": [
                {
                    "id": str(association_id),
                    "from_feature_id": str(feature_id),
                    "to_feature_id": str(connected_feature_id),
                    "association_type": "connectivity",
                    "version": 1,
                }
            ],
        }
    )
    repository = WorkOrderRepository(session)

    aggregate = asyncio.run(
        repository.get_workspace_aggregate(
            work_order_id=work_order_id,
            edit_version_id=edit_version_id,
        )
    )

    assert aggregate is not None
    assert len(session.execute_calls) == 1
    assert session.execute_calls[0] == (
        WORKSPACE_AGGREGATE_SQL,
        {
            "work_order_id": work_order_id,
            "edit_version_id": edit_version_id,
        },
    )
    assert session.scalars_calls == []
    assert aggregate.work_order.id == work_order_id
    assert aggregate.work_order.code == "WO-001"
    assert aggregate.work_order.status is WorkOrderStatus.IN_PROGRESS
    assert aggregate.work_order.assignee_user_id == assignee_user_id
    assert aggregate.edit_version.id == edit_version_id
    assert aggregate.edit_version.status is EditVersionStatus.OPEN
    assert aggregate.edit_version.base_network_revision == 12
    assert aggregate.aoi.id == aoi_id
    assert aggregate.aoi.extent == [65.495, 44.795, 65.545, 44.835]
    assert aggregate.features_data[0]["asset_code"] == "J-001"
    assert aggregate.associations_data[0]["id"] == str(association_id)


def test_get_workspace_aggregate_returns_none_when_sql_finds_no_context() -> None:
    repository = WorkOrderRepository(FakeSession(None))

    aggregate = asyncio.run(
        repository.get_workspace_aggregate(
            work_order_id=uuid4(),
            edit_version_id=uuid4(),
        )
    )

    assert aggregate is None
```

- [ ] **Step 2: Run the unit test and verify it fails before implementation**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py -q"
```

Expected before implementation:

```text
ImportError or AttributeError for WORKSPACE_AGGREGATE_SQL_PATH / WORKSPACE_AGGREGATE_SQL
```

### Task 2: Add Association Filtering Regression Coverage

**Files:**
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Add imports required by the regression test**

In `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`, update imports near the top:

```python
from uuid import uuid4

from geoalchemy2.elements import WKTElement
```

Update the existing utility-network model import block so it includes `AssociationType` and `FeatureType`:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    FeatureType,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
```

- [ ] **Step 2: Add the regression test after `test_seed_chain_workspace_aggregate_returns_work_order_scope`**

Paste this test function:

```python
def test_workspace_aggregate_excludes_association_when_endpoint_feature_is_outside_aoi() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        assignee_id = next(
            spec.id
            for spec in SEED_DEMO_USER_SPECS
            if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
        )
        result = await EditVersionService(
            session,
            UserRepository(session),
            WorkOrderRepository(session),
            DefaultStateRepository(session),
        ).open_for_work_order(SEED_WORK_ORDER_SPEC.id, assignee_id)

        inside_feature = await session.scalar(
            select(EditVersionFeature)
            .where(EditVersionFeature.edit_version_id == result.edit_version.id)
            .order_by(EditVersionFeature.asset_code)
        )
        assert inside_feature is not None

        outside_feature_id = uuid4()
        outside_association_id = uuid4()
        session.add(
            EditVersionFeature(
                edit_version_id=result.edit_version.id,
                feature_id=outside_feature_id,
                asset_code="OUTSIDE-AOI-001",
                feature_type=FeatureType.JUNCTION,
                geometry=WKTElement("SRID=4326;POINT(66 45)", extended=True),
                properties={"name": "Outside AOI"},
                network_version=1,
            )
        )
        await session.flush()
        session.add(
            EditVersionAssociation(
                edit_version_id=result.edit_version.id,
                association_id=outside_association_id,
                association_type=AssociationType.CONNECTIVITY,
                from_feature_id=inside_feature.feature_id,
                to_feature_id=outside_feature_id,
                properties={"reason": "endpoint outside AOI"},
                network_version=1,
            )
        )
        await session.flush()

        aggregate = await WorkOrderRepository(session).get_workspace_aggregate(
            work_order_id=SEED_WORK_ORDER_SPEC.id,
            edit_version_id=result.edit_version.id,
        )

        assert aggregate is not None
        feature_ids = {str(feature["id"]) for feature in aggregate.features_data}
        association_ids = {str(association["id"]) for association in aggregate.associations_data}
        assert str(outside_feature_id) not in feature_ids
        assert str(outside_association_id) not in association_ids
        assert len(aggregate.features_data) == 19
        assert len(aggregate.associations_data) == 9

    run_in_rollback_transaction(scenario)
```

- [ ] **Step 3: Run the regression test before the refactor**

Run:

```powershell
$databaseUrl = docker exec utility_service printenv DATABASE_URL
docker run --rm --network infra_default -v C:\Repositories\geoservice\apps\backend:/app -w /app -e RUN_DB_TESTS=1 -e DATABASE_URL="$($databaseUrl.Trim())" --entrypoint bash utility_service:dev -lc "pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_workspace_aggregate_excludes_association_when_endpoint_feature_is_outside_aoi -q"
```

Expected before implementation:

```text
1 passed
```

This regression protects behavior that already exists. It is allowed to pass before the raw SQL refactor because its job is to prevent the refactor from widening association membership.

### Task 3: Add `workspace_aggregate.sql`

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql`

- [ ] **Step 1: Create the SQL file**

Create `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql` with this content:

```sql
WITH workspace_context AS (
    SELECT
        work_order.id AS work_order_id,
        work_order.code AS work_order_code,
        work_order.title AS work_order_title,
        work_order.description AS work_order_description,
        work_order.status AS work_order_status,
        work_order.assignee_user_id AS work_order_assignee_user_id,
        edit_version.id AS edit_version_id,
        edit_version.status AS edit_version_status,
        edit_version.base_network_revision AS edit_version_base_network_revision,
        aoi.id AS aoi_id,
        aoi.name AS aoi_name,
        aoi.description AS aoi_description,
        aoi.geometry AS aoi_geometry
    FROM work_order.work_orders AS work_order
    JOIN work_order.edit_versions AS edit_version
      ON edit_version.work_order_id = work_order.id
    JOIN work_order.aois AS aoi
      ON aoi.id = work_order.aoi_id
    WHERE work_order.id = :work_order_id
      AND edit_version.id = :edit_version_id
),
workspace_features AS MATERIALIZED (
    SELECT
        feature.edit_version_id,
        feature.feature_id,
        feature.asset_code,
        feature.feature_type,
        feature.geometry,
        feature.properties,
        feature.network_version,
        feature.operation
    FROM workspace_context AS context
    JOIN work_order.edit_version_features AS feature
      ON feature.edit_version_id = context.edit_version_id
    WHERE ST_Intersects(context.aoi_geometry, feature.geometry)
),
features_json AS (
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', feature.feature_id,
                'asset_code', feature.asset_code,
                'feature_type', feature.feature_type,
                'geometry_data', ST_AsGeoJSON(feature.geometry)::jsonb,
                'properties', feature.properties,
                'network_version', feature.network_version,
                'operation', feature.operation
            )
            ORDER BY feature.asset_code, feature.feature_id
        ),
        '[]'::jsonb
    ) AS features_data
    FROM workspace_features AS feature
),
associations_json AS (
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', association.association_id,
                'from_feature_id', association.from_feature_id,
                'to_feature_id', association.to_feature_id,
                'association_type', association.association_type,
                'version', association.network_version
            )
            ORDER BY
                association.from_feature_id,
                association.to_feature_id,
                association.association_type,
                association.association_id
        ),
        '[]'::jsonb
    ) AS associations_data
    FROM workspace_context AS context
    JOIN work_order.edit_version_associations AS association
      ON association.edit_version_id = context.edit_version_id
    JOIN workspace_features AS from_feature
      ON from_feature.feature_id = association.from_feature_id
    JOIN workspace_features AS to_feature
      ON to_feature.feature_id = association.to_feature_id
)
SELECT
    context.work_order_id,
    context.work_order_code,
    context.work_order_title,
    context.work_order_description,
    context.work_order_status,
    context.work_order_assignee_user_id,
    context.edit_version_id,
    context.edit_version_status,
    context.edit_version_base_network_revision,
    context.aoi_id,
    context.aoi_name,
    context.aoi_description,
    ST_AsGeoJSON(context.aoi_geometry)::jsonb AS aoi_geometry_data,
    jsonb_build_array(
        ST_XMin(Box2D(context.aoi_geometry)),
        ST_YMin(Box2D(context.aoi_geometry)),
        ST_XMax(Box2D(context.aoi_geometry)),
        ST_YMax(Box2D(context.aoi_geometry))
    ) AS aoi_extent,
    features_json.features_data,
    associations_json.associations_data
FROM workspace_context AS context
CROSS JOIN features_json
CROSS JOIN associations_json
```

- [ ] **Step 2: Run the SQL contract test and verify it reaches repository mapping failure**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py::test_workspace_aggregate_sql_lives_in_sql_file -q"
```

Expected after creating the SQL file and before repository refactor:

```text
1 passed
```

### Task 4: Refactor `WorkOrderRepository.get_workspace_aggregate()`

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`

- [ ] **Step 1: Replace imports at the top of the file**

Use this import block:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import Integer, String, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
```

- [ ] **Step 2: Add SQL path, typed statement, and row dataclasses above `WorkspaceAoiRow`**

Add this code after imports and before `WorkspaceAoiRow`:

```python
WORKSPACE_AGGREGATE_SQL_PATH = (
    Path(__file__).resolve().parents[1] / "sql" / "workspace_aggregate.sql"
)

WORKSPACE_AGGREGATE_SQL = text(
    WORKSPACE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")
).columns(
    work_order_id=PGUUID(as_uuid=True),
    work_order_code=String(),
    work_order_title=String(),
    work_order_description=String(),
    work_order_status=String(),
    work_order_assignee_user_id=PGUUID(as_uuid=True),
    edit_version_id=PGUUID(as_uuid=True),
    edit_version_status=String(),
    edit_version_base_network_revision=Integer(),
    aoi_id=PGUUID(as_uuid=True),
    aoi_name=String(),
    aoi_description=String(),
    aoi_geometry_data=JSONB(),
    aoi_extent=JSONB(),
    features_data=JSONB(),
    associations_data=JSONB(),
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
```

- [ ] **Step 3: Update `WorkspaceAggregateRow` field types**

Replace the existing dataclass with:

```python
@dataclass(frozen=True)
class WorkspaceAggregateRow:
    work_order: WorkspaceWorkOrderRow
    edit_version: WorkspaceEditVersionRow
    aoi: WorkspaceAoiRow
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]
```

- [ ] **Step 4: Replace the body of `get_workspace_aggregate()`**

Replace the entire current method body with:

```python
        result = await self.session.execute(
            WORKSPACE_AGGREGATE_SQL,
            {
                "work_order_id": work_order_id,
                "edit_version_id": edit_version_id,
            },
        )
        row = result.mappings().one_or_none()
        if row is None:
            return None
        return WorkspaceAggregateRow(
            work_order=WorkspaceWorkOrderRow(
                id=row["work_order_id"],
                code=row["work_order_code"],
                title=row["work_order_title"],
                description=row["work_order_description"],
                status=WorkOrderStatus(row["work_order_status"]),
                assignee_user_id=row["work_order_assignee_user_id"],
            ),
            edit_version=WorkspaceEditVersionRow(
                id=row["edit_version_id"],
                status=EditVersionStatus(row["edit_version_status"]),
                base_network_revision=row["edit_version_base_network_revision"],
            ),
            aoi=WorkspaceAoiRow(
                id=row["aoi_id"],
                name=row["aoi_name"],
                description=row["aoi_description"],
                geometry_data=row["aoi_geometry_data"],
                extent=row["aoi_extent"],
            ),
            features_data=row["features_data"],
            associations_data=row["associations_data"],
        )
```

- [ ] **Step 5: Run the repository unit tests and verify they pass**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_default_state_repository.py -q"
```

Expected:

```text
all selected tests pass
```

### Task 5: Run Integration And Smoke-Scope Verification

**Files:**
- Test: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
- Test: `apps/backend/tests/smoke/test_full_path_workspace_smoke.py`
- Smoke runner remains unchanged: `apps/backend/tests/smoke/full_path_workspace_smoke.py`

- [ ] **Step 1: Run the focused seed-chain workspace tests against the current dev DB**

Run:

```powershell
$databaseUrl = docker exec utility_service printenv DATABASE_URL
docker run --rm --network infra_default -v C:\Repositories\geoservice\apps\backend:/app -w /app -e RUN_DB_TESTS=1 -e DATABASE_URL="$($databaseUrl.Trim())" --entrypoint bash utility_service:dev -lc "pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_seed_chain_workspace_aggregate_returns_work_order_scope tests/integration_tests/test_work_order_seed_chain_integration.py::test_workspace_aggregate_excludes_association_when_endpoint_feature_is_outside_aoi -q"
```

Expected:

```text
2 passed
```

- [ ] **Step 2: Run the whole seed-chain integration file**

Run:

```powershell
$databaseUrl = docker exec utility_service printenv DATABASE_URL
docker run --rm --network infra_default -v C:\Repositories\geoservice\apps\backend:/app -w /app -e RUN_DB_TESTS=1 -e DATABASE_URL="$($databaseUrl.Trim())" --entrypoint bash utility_service:dev -lc "pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q"
```

Expected:

```text
all tests in the file pass
```

- [ ] **Step 3: Run the smoke-runner unit tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest tests/smoke/test_full_path_workspace_smoke.py -q"
```

Expected:

```text
all selected smoke-runner tests pass
```

- [ ] **Step 4: Run metadata and migration index contract tests to keep the precondition green**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_network_model_metadata.py tests/integration_tests/test_edit_version_migration.py -q"
```

Expected without `RUN_DB_TESTS=1`:

```text
metadata tests pass and DB migration tests skip
```

### Task 6: Format, Lint, And Inspect SQL Shape

**Files:**
- Modified backend Python files and new SQL file.

- [ ] **Step 1: Run `black --check` on changed Python files**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black --check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_network_model_metadata.py tests/integration_tests/test_edit_version_migration.py tests/integration_tests/test_work_order_seed_chain_integration.py"
```

Expected:

```text
All done
```

- [ ] **Step 2: Run `ruff check` on changed Python files**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "ruff check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_network_model_metadata.py tests/integration_tests/test_edit_version_migration.py tests/integration_tests/test_work_order_seed_chain_integration.py"
```

Expected:

```text
All checks passed
```

- [ ] **Step 3: Inspect generated SQL contract with `rg`**

Run:

```powershell
rg -n "workspace_features AS MATERIALIZED|JOIN workspace_features AS from_feature|JOIN workspace_features AS to_feature|features_json|associations_json" apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql
```

Expected:

```text
The SQL file contains all five searched terms.
```

- [ ] **Step 4: Run whitespace diff check**

Run:

```powershell
git diff --check
```

Expected:

```text
no output
```

### Task 7: Update Durable Code Wiki Notes

**Files:**
- Modify: `Code_wiki/архитектура/data_model.md`
- Modify: `Code_wiki/правила_и_стиль/testing_strategy.md`
- Modify: `Code_wiki/сборка/ci_and_quality.md`
- Modify: `Code_wiki/состояние_проекта/repository_change_ingest.md`
- Modify: `Code_wiki/index.md`

- [ ] **Step 1: Update `Code_wiki/архитектура/data_model.md`**

Change the frontmatter:

```yaml
updated: 2026-07-09
source: repository-change:2026-07-09
```

In `## Spatial Queries`, replace the paragraph about `WorkOrderRepository.get_workspace_aggregate` with this text:

```markdown
`WorkOrderRepository.get_workspace_aggregate` читает workspace для пары
`work_order_id`/`edit_version_id` через
`utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql`.
Raw SQL использует `workspace_context`, затем
`workspace_features AS MATERIALIZED`, где features из
`work_order.edit_version_features` один раз фильтруются по
`WorkOrder.scope.aoi` через `ST_Intersects`. `features_json` собирает JSONB
features из materialized набора, а `associations_json` добавляет только связи,
у которых оба endpoint feature найдены через join к `workspace_features`.
Запрос возвращает `WorkOrder`, `EditVersion`, `work_order.AOI`, GeoJSON AOI,
extent, `features_data` и `associations_data` одним DB round trip.
```

- [ ] **Step 2: Update `Code_wiki/правила_и_стиль/testing_strategy.md`**

Change the frontmatter:

```yaml
updated: 2026-07-09
source: repository-change:2026-07-09
```

Add this backend coverage bullet near the existing workspace and migration coverage bullets:

```markdown
- workspace aggregate repository tests проверяют, что raw SQL живет в
  `sql/workspace_aggregate.sql`, содержит `workspace_features AS MATERIALIZED`,
  выполняется одним `execute` round trip и мапится в `WorkspaceAggregateRow`;
```

- [ ] **Step 3: Update `Code_wiki/сборка/ci_and_quality.md`**

Change the frontmatter:

```yaml
updated: 2026-07-09
source: repository-change:2026-07-09
```

Add this sentence after the paragraph describing full path workspace API smoke:

```markdown
Focused backend verification for workspace aggregate raw SQL includes
`pytest utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py -q`
and the seed-chain workspace tests in
`tests/integration_tests/test_work_order_seed_chain_integration.py`.
```

- [ ] **Step 4: Add a compact repository-change row**

In `Code_wiki/состояние_проекта/repository_change_ingest.md`, change frontmatter to:

```yaml
updated: 2026-07-09
source: repository-change:2026-07-09
```

Add this row at the top of the active registry table:

```markdown
| 2026-07-09 | [[архитектура/data_model]], [[правила_и_стиль/testing_strategy]], [[сборка/ci_and_quality]] | Workspace aggregate read path вынесен в `sql/workspace_aggregate.sql`: запрос использует `workspace_features AS MATERIALIZED`, собирает `features_data` и `associations_data` из одного materialized workspace feature set и сохраняет текущий `GET .../workspace` response contract одним DB round trip. | repository-change:2026-07-09 workspace-aggregate-raw-sql |
```

- [ ] **Step 5: Add the fresh knowledge entry to `Code_wiki/index.md`**

Change frontmatter to:

```yaml
updated: 2026-07-09
source: repository-change:2026-07-09
```

Add this entry at the top of `## Свежие Repository-Change Знания`:

```markdown
- 2026-07-09: [[архитектура/data_model]], [[правила_и_стиль/testing_strategy]]
  и [[сборка/ci_and_quality]] отражают raw SQL workspace aggregate:
  `sql/workspace_aggregate.sql` использует
  `workspace_features AS MATERIALIZED`, переиспользует один workspace feature
  set для features и associations и сохраняет публичный `GET .../workspace`
  contract.
```

- [ ] **Step 6: Run wiki lint and report known RAW issues accurately**

Run:

```powershell
C:\Users\dimon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts/lint-wiki.py --root .
```

Expected in the current repository state:

```text
The command exits non-zero only for the known RAW_inputs missing_frontmatter issues recorded in memory/project-state.md.
```

Do not edit `RAW_inputs/*` in this task.

### Task 8: Final Verification Before Handoff

**Files:**
- All changed files.

- [ ] **Step 1: Run the focused backend verification set**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_default_state_repository.py utility_service/infrastructure/tests/test_network_model_metadata.py tests/smoke/test_full_path_workspace_smoke.py -q"
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 2: Run the DB-backed integration tests**

Run:

```powershell
$databaseUrl = docker exec utility_service printenv DATABASE_URL
docker run --rm --network infra_default -v C:\Repositories\geoservice\apps\backend:/app -w /app -e RUN_DB_TESTS=1 -e DATABASE_URL="$($databaseUrl.Trim())" --entrypoint bash utility_service:dev -lc "pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q"
```

Expected:

```text
all selected integration tests pass
```

- [ ] **Step 3: Run style checks**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black --check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_network_model_metadata.py tests/integration_tests/test_edit_version_migration.py tests/integration_tests/test_work_order_seed_chain_integration.py && ruff check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py utility_service/infrastructure/tests/test_network_model_metadata.py tests/integration_tests/test_edit_version_migration.py tests/integration_tests/test_work_order_seed_chain_integration.py"
```

Expected:

```text
black reports files would be left unchanged and ruff reports All checks passed
```

- [ ] **Step 4: Inspect final status and diff**

Run:

```powershell
git status --short
git diff --stat
git diff --check
```

Expected:

```text
Only intended code, SQL, test, plan, spec, and Code_wiki files are modified or untracked.
git diff --check produces no output.
```

## Self-Review

**Spec coverage:** The plan covers the approved raw SQL file, `workspace_features AS MATERIALIZED`, JSON feature and association assembly through that CTE, repository mapping, unchanged API/service/frontend contract, index precondition verification, association endpoint filtering regression, smoke-scope verification, and Code_wiki repository-change update.

**Placeholder scan:** The plan contains complete code blocks, concrete test commands, concrete expected results, and no references to undefined functions that are introduced only later. The only future work mentioned is explicitly out of this plan's execution path.

**Type consistency:** `WorkspaceWorkOrderRow.status` is `WorkOrderStatus`, `WorkspaceEditVersionRow.status` is `EditVersionStatus`, and `WorkspaceService` can continue using `.status.value`. Raw SQL JSON keys match current `WorkspaceService.feature_properties()` and `WorkspaceAssociationOut` input keys: `id`, `asset_code`, `feature_type`, `geometry_data`, `properties`, `network_version`, `operation`, `from_feature_id`, `to_feature_id`, `association_type`, and `version`.
