# Cross-Context Consistency Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only operational checker that reports broken cross-context UUID links without adding cross-schema FK constraints.

**Architecture:** Add a focused PostgreSQL infrastructure component with explicit SQL probes, dataclass contracts in a dedicated `consistency/contracts` package, DB integration coverage, a smoke runner, and CI wiring. The checker returns facts about data integrity and does not map issues to HTTP/domain errors.

**Tech Stack:** Python 3.12, async SQLAlchemy, PostgreSQL/PostGIS, pytest, Docker Compose CI.

---

## File Structure

Create:

- `apps/backend/utility_service/infrastructure/postgresql/consistency/__init__.py`
  - Public exports for the consistency package.
- `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/__init__.py`
  - Public exports for consistency dataclass contracts.
- `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/check.py`
  - `Severity` and `CrossContextConsistencyCheck` dataclass contract.
- `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/report.py`
  - `CrossContextConsistencyIssue` and `CrossContextConsistencyReport` dataclass contracts.
- `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checks.py`
  - Registry of explicit read-only SQL checks using the check contract.
- `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checker.py`
  - Checker runner, issue creation, subset selection.
- `apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py`
  - Unit tests for report assembly, subset selection, and check registry.
- `apps/backend/tests/integration_tests/test_cross_context_consistency.py`
  - PostgreSQL integration tests for clean seeded state and negative data corruption cases.
- `apps/backend/tests/smoke/cross_context_consistency_smoke.py`
  - Live read-only smoke runner for compose environments.
- `apps/backend/tests/smoke/test_cross_context_consistency_smoke.py`
  - Unit tests for smoke report formatting and exit code.

Modify:

- `.github/workflows/ci.yml`
  - Add `tests/integration_tests/test_cross_context_consistency.py` to the existing compose DB integration step.

Do not modify:

- Alembic migrations.
- Existing SQLAlchemy model FK definitions.
- Existing service-level errors or HTTP handlers.
- Domain write paths.

---

### Task 1: Checker Unit Tests

**Files:**
- Create: `apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py`

- [ ] **Step 1: Write the failing unit tests**

Create `apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py`:

```python
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from utility_service.infrastructure.postgresql.consistency.cross_context_checker import (
    CrossContextConsistencyChecker,
    UnknownCrossContextConsistencyCheckError,
)
from utility_service.infrastructure.postgresql.consistency.cross_context_checks import (
    DEFAULT_CROSS_CONTEXT_CHECKS,
)
from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
)


class FakeMappingResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def all(self) -> list[dict]:
        return self.rows


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def mappings(self) -> FakeMappingResult:
        return FakeMappingResult(self.rows)


class FakeSession:
    def __init__(self, rows_by_call: list[list[dict]]) -> None:
        self.rows_by_call = list(rows_by_call)
        self.execute_calls: list[tuple[object, dict]] = []

    async def execute(self, statement, params):  # type: ignore[no-untyped-def]
        self.execute_calls.append((statement, params))
        return FakeResult(self.rows_by_call.pop(0))


def sample_check(name: str = "sample_check") -> CrossContextConsistencyCheck:
    return CrossContextConsistencyCheck(
        name=name,
        severity="error",
        message="Sample check failed.",
        source="source.table.source_id",
        target="target.table.id",
        sql=text("select 1"),
        sample_fields={
            "source_id": "sourceId",
            "target_id": "targetId",
        },
        sample_limit=5,
    )


def test_clean_check_result_builds_ok_report() -> None:
    checked_at = datetime(2026, 7, 6, 10, 0, tzinfo=timezone.utc)
    session = FakeSession(rows_by_call=[[]])
    check = sample_check()

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[check],
            clock=lambda: checked_at,
        ).run()
    )

    assert report.ok is True
    assert report.checked_at == checked_at
    assert report.checks_run == 1
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.issues == []
    assert session.execute_calls == [(check.sql, {"sample_limit": 5})]


def test_rows_build_issue_with_count_and_human_readable_sample_rows() -> None:
    source_id = uuid4()
    target_id = uuid4()
    session = FakeSession(
        rows_by_call=[
            [
                {
                    "issue_count": 2,
                    "source_id": source_id,
                    "target_id": target_id,
                },
                {
                    "issue_count": 2,
                    "source_id": uuid4(),
                    "target_id": uuid4(),
                },
            ]
        ]
    )

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[sample_check()],
        ).run()
    )

    assert report.ok is False
    assert report.error_count == 1
    assert report.warning_count == 0
    assert len(report.issues) == 1
    issue = report.issues[0]
    assert issue.check_name == "sample_check"
    assert issue.severity == "error"
    assert issue.message == "Sample check failed."
    assert issue.source == "source.table.source_id"
    assert issue.target == "target.table.id"
    assert issue.count == 2
    assert issue.sample_rows[0] == {
        "sourceId": str(source_id),
        "targetId": str(target_id),
    }


def test_subset_run_executes_only_named_checks() -> None:
    first = sample_check("first_check")
    second = sample_check("second_check")
    session = FakeSession(rows_by_call=[[]])

    report = asyncio.run(
        CrossContextConsistencyChecker(
            session,
            checks=[first, second],
        ).run(["second_check"])
    )

    assert report.ok is True
    assert report.checks_run == 1
    assert session.execute_calls == [(second.sql, {"sample_limit": 5})]


def test_unknown_subset_check_name_fails_with_known_names() -> None:
    checker = CrossContextConsistencyChecker(
        FakeSession(rows_by_call=[]),
        checks=[sample_check("known_check")],
    )

    with pytest.raises(
        UnknownCrossContextConsistencyCheckError,
        match="Unknown cross-context consistency checks: missing_check. Known checks: known_check",
    ):
        asyncio.run(checker.run(["missing_check"]))


def test_default_cross_context_check_registry_contains_first_increment_contract() -> None:
    assert {check.name for check in DEFAULT_CROSS_CONTEXT_CHECKS} == {
        "work_order_assignee_user_exists",
        "work_order_created_by_user_exists",
        "default_state_work_order_exists",
        "edit_version_owner_user_exists",
        "edit_version_default_state_exists",
        "edit_version_default_state_matches_work_order",
    }
    assert {check.severity for check in DEFAULT_CROSS_CONTEXT_CHECKS} == {"error"}
    assert all(check.sample_limit == 10 for check in DEFAULT_CROSS_CONTEXT_CHECKS)
```

- [ ] **Step 2: Run the unit test to verify it fails**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_cross_context_checker.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `utility_service.infrastructure.postgresql.consistency`.

---

### Task 2: Checker Core And SQL Registry

**Files:**
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/__init__.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/__init__.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/check.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/report.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checks.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checker.py`
- Test: `apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py`

- [ ] **Step 1: Add dataclass contracts**

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/check.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from sqlalchemy.sql.elements import TextClause


Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class CrossContextConsistencyCheck:
    name: str
    severity: Severity
    message: str
    source: str
    target: str | None
    sql: TextClause
    sample_fields: Mapping[str, str]
    sample_limit: int = 10
```

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/report.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from utility_service.infrastructure.postgresql.consistency.contracts.check import Severity


@dataclass(frozen=True)
class CrossContextConsistencyIssue:
    check_name: str
    severity: Severity
    message: str
    source: str
    target: str | None
    count: int
    sample_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class CrossContextConsistencyReport:
    ok: bool
    checked_at: datetime
    checks_run: int
    error_count: int
    warning_count: int
    issues: list[CrossContextConsistencyIssue]
```

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/contracts/__init__.py`:

```python
from utility_service.infrastructure.postgresql.consistency.contracts.check import (
    CrossContextConsistencyCheck,
    Severity,
)
from utility_service.infrastructure.postgresql.consistency.contracts.report import (
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)

__all__ = [
    "CrossContextConsistencyCheck",
    "CrossContextConsistencyIssue",
    "CrossContextConsistencyReport",
    "Severity",
]
```

- [ ] **Step 2: Add the check registry**

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checks.py`:

```python
from __future__ import annotations

from sqlalchemy import text

from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
)


DEFAULT_CROSS_CONTEXT_CHECKS = (
    CrossContextConsistencyCheck(
        name="work_order_assignee_user_exists",
        severity="error",
        message="WorkOrder assignee_user_id ссылается на отсутствующего пользователя.",
        source="work_order.work_orders.assignee_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              wo.id as work_order_id,
              wo.assignee_user_id as assignee_user_id
            from work_order.work_orders wo
            left join "user".users u on u.id = wo.assignee_user_id
            where u.id is null
            order by wo.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "work_order_id": "workOrderId",
            "assignee_user_id": "assigneeUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="work_order_created_by_user_exists",
        severity="error",
        message="WorkOrder created_by_user_id ссылается на отсутствующего пользователя.",
        source="work_order.work_orders.created_by_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              wo.id as work_order_id,
              wo.created_by_user_id as created_by_user_id
            from work_order.work_orders wo
            left join "user".users u on u.id = wo.created_by_user_id
            where u.id is null
            order by wo.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "work_order_id": "workOrderId",
            "created_by_user_id": "createdByUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="default_state_work_order_exists",
        severity="error",
        message="DefaultState work_order_id ссылается на отсутствующий WorkOrder.",
        source="utility_network.default_states.work_order_id",
        target="work_order.work_orders.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ds.id as default_state_id,
              ds.work_order_id as work_order_id
            from utility_network.default_states ds
            left join work_order.work_orders wo on wo.id = ds.work_order_id
            where wo.id is null
            order by ds.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "default_state_id": "defaultStateId",
            "work_order_id": "workOrderId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_owner_user_exists",
        severity="error",
        message="EditVersion owner_user_id ссылается на отсутствующего пользователя.",
        source="work_order.edit_versions.owner_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.owner_user_id as owner_user_id
            from work_order.edit_versions ev
            left join "user".users u on u.id = ev.owner_user_id
            where u.id is null
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "owner_user_id": "ownerUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_default_state_exists",
        severity="error",
        message="EditVersion default_state_id ссылается на отсутствующий DefaultState.",
        source="work_order.edit_versions.default_state_id",
        target="utility_network.default_states.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.default_state_id as default_state_id
            from work_order.edit_versions ev
            left join utility_network.default_states ds on ds.id = ev.default_state_id
            where ds.id is null
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "default_state_id": "defaultStateId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_default_state_matches_work_order",
        severity="error",
        message="EditVersion default_state_id указывает на DefaultState другого WorkOrder.",
        source="work_order.edit_versions.default_state_id",
        target="utility_network.default_states.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.work_order_id as edit_version_work_order_id,
              ev.default_state_id as default_state_id,
              ds.work_order_id as default_state_work_order_id
            from work_order.edit_versions ev
            join utility_network.default_states ds on ds.id = ev.default_state_id
            where ds.work_order_id <> ev.work_order_id
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "edit_version_work_order_id": "editVersionWorkOrderId",
            "default_state_id": "defaultStateId",
            "default_state_work_order_id": "defaultStateWorkOrderId",
        },
    ),
)
```

- [ ] **Step 3: Add the checker implementation**

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/cross_context_checker.py`:

```python
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.consistency.cross_context_checks import (
    DEFAULT_CROSS_CONTEXT_CHECKS,
)
from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)


class UnknownCrossContextConsistencyCheckError(ValueError):
    """Raised when a caller asks for a check name that is not registered."""


class CrossContextConsistencyChecker:
    def __init__(
        self,
        session: AsyncSession,
        *,
        checks: Sequence[CrossContextConsistencyCheck] = DEFAULT_CROSS_CONTEXT_CHECKS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.session = session
        self._checks = list(checks)
        self._checks_by_name = {check.name: check for check in self._checks}
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def run(
        self,
        check_names: Sequence[str] | None = None,
    ) -> CrossContextConsistencyReport:
        selected_checks = self._select_checks(check_names)
        issues: list[CrossContextConsistencyIssue] = []

        for check in selected_checks:
            issue = await self._run_check(check)
            if issue is not None:
                issues.append(issue)

        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        return CrossContextConsistencyReport(
            ok=error_count == 0,
            checked_at=self._clock(),
            checks_run=len(selected_checks),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
        )

    def _select_checks(
        self,
        check_names: Sequence[str] | None,
    ) -> list[CrossContextConsistencyCheck]:
        if check_names is None:
            return list(self._checks)

        unknown_names = [name for name in check_names if name not in self._checks_by_name]
        if unknown_names:
            known_names = ", ".join(sorted(self._checks_by_name))
            missing_names = ", ".join(unknown_names)
            raise UnknownCrossContextConsistencyCheckError(
                "Unknown cross-context consistency checks: "
                f"{missing_names}. Known checks: {known_names}"
            )

        return [self._checks_by_name[name] for name in check_names]

    async def _run_check(
        self,
        check: CrossContextConsistencyCheck,
    ) -> CrossContextConsistencyIssue | None:
        result = await self.session.execute(
            check.sql,
            {"sample_limit": check.sample_limit},
        )
        rows = list(result.mappings().all())
        if not rows:
            return None

        return CrossContextConsistencyIssue(
            check_name=check.name,
            severity=check.severity,
            message=check.message,
            source=check.source,
            target=check.target,
            count=int(rows[0]["issue_count"]),
            sample_rows=[self._sample_row(check, row) for row in rows],
        )

    def _sample_row(
        self,
        check: CrossContextConsistencyCheck,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            output_name: self._jsonable_value(row[input_name])
            for input_name, output_name in check.sample_fields.items()
        }

    def _jsonable_value(self, value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value
```

- [ ] **Step 4: Add package exports**

Create `apps/backend/utility_service/infrastructure/postgresql/consistency/__init__.py`:

```python
from utility_service.infrastructure.postgresql.consistency.cross_context_checker import (
    CrossContextConsistencyChecker,
    UnknownCrossContextConsistencyCheckError,
)
from utility_service.infrastructure.postgresql.consistency.cross_context_checks import (
    DEFAULT_CROSS_CONTEXT_CHECKS,
)
from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
    Severity,
)

__all__ = [
    "CrossContextConsistencyCheck",
    "CrossContextConsistencyChecker",
    "CrossContextConsistencyIssue",
    "CrossContextConsistencyReport",
    "DEFAULT_CROSS_CONTEXT_CHECKS",
    "Severity",
    "UnknownCrossContextConsistencyCheckError",
]
```

- [ ] **Step 5: Run the checker unit tests**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_cross_context_checker.py -q
```

Expected: PASS.

- [ ] **Step 6: Run formatting and lint on the new package**

Run:

```powershell
cd apps/backend
black --check utility_service/infrastructure/postgresql/consistency utility_service/infrastructure/tests/test_cross_context_checker.py
ruff check utility_service/infrastructure/postgresql/consistency utility_service/infrastructure/tests/test_cross_context_checker.py
```

Expected: both commands PASS. If Black reports formatting changes, run:

```powershell
cd apps/backend
black utility_service/infrastructure/postgresql/consistency utility_service/infrastructure/tests/test_cross_context_checker.py
```

Then repeat the `black --check` and `ruff check` commands.

---

### Task 3: PostgreSQL Integration Tests

**Files:**
- Create: `apps/backend/tests/integration_tests/test_cross_context_consistency.py`
- Test: `apps/backend/tests/integration_tests/test_cross_context_consistency.py`

- [ ] **Step 1: Write the integration tests**

Create `apps/backend/tests/integration_tests/test_cross_context_consistency.py`:

```python
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_utility_dataset_repository import SeedUtilityDatasetRepository
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.services.seed_work_order_service import SeedWorkOrderService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC
from tests.integration_tests.network_db_support import run_in_rollback_transaction
from utility_service.infrastructure.postgresql.consistency import (
    CrossContextConsistencyChecker,
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)
from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateStatus,
)
from utility_service.infrastructure.postgresql.models.work_order import EditVersion
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService


async def ensure_seed_chain(session: AsyncSession) -> None:
    await SeedDemoUserService(
        session,
        SeedUserRepository(session),
    ).ensure_demo_users()
    await SeedUtilityDatasetService(
        session,
        SeedUtilityDatasetRepository(session),
    ).ensure_utility_dataset()
    await SeedWorkOrderService(
        session,
        SeedWorkOrderRepository(session),
        SeedUserRepository(session),
        SeedUtilityDatasetRepository(session),
    ).ensure_work_order()


async def ensure_open_seed_edit_version(session: AsyncSession) -> EditVersion:
    await ensure_seed_chain(session)
    assignee_id = next(
        spec.id for spec in SEED_DEMO_USER_SPECS if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
    )
    result = await EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        DefaultStateRepository(session),
    ).open_for_work_order(SEED_WORK_ORDER_SPEC.id, assignee_id)
    return result.edit_version


def issue_by_name(
    report: CrossContextConsistencyReport,
    check_name: str,
) -> CrossContextConsistencyIssue:
    matching = [issue for issue in report.issues if issue.check_name == check_name]
    assert len(matching) == 1, report.issues
    return matching[0]


def test_seeded_database_has_consistent_cross_context_links() -> None:
    async def scenario(session: AsyncSession) -> None:
        await ensure_seed_chain(session)

        report = await CrossContextConsistencyChecker(session).run()

        assert report.ok is True
        assert report.error_count == 0
        assert report.warning_count == 0
        assert report.issues == []

    run_in_rollback_transaction(scenario)


def test_checker_reports_orphan_edit_version_owner_user() -> None:
    async def scenario(session: AsyncSession) -> None:
        edit_version = await ensure_open_seed_edit_version(session)
        missing_user_id = uuid4()
        edit_version.owner_user_id = missing_user_id
        await session.flush()

        report = await CrossContextConsistencyChecker(session).run(
            ["edit_version_owner_user_exists"]
        )

        assert report.ok is False
        issue = issue_by_name(report, "edit_version_owner_user_exists")
        assert issue.count == 1
        assert issue.sample_rows == [
            {
                "editVersionId": str(edit_version.id),
                "ownerUserId": str(missing_user_id),
            }
        ]

    run_in_rollback_transaction(scenario)


def test_checker_reports_edit_version_default_state_work_order_mismatch() -> None:
    async def scenario(session: AsyncSession) -> None:
        edit_version = await ensure_open_seed_edit_version(session)
        original_default_state = await session.scalar(
            select(DefaultState).where(DefaultState.id == edit_version.default_state_id)
        )
        assert original_default_state is not None
        mismatched_work_order_id = uuid4()
        mismatched_default_state = DefaultState(
            work_order_id=mismatched_work_order_id,
            network_state_id=original_default_state.network_state_id,
            base_network_revision=original_default_state.base_network_revision,
            status=DefaultStateStatus.ACTIVE,
        )
        session.add(mismatched_default_state)
        await session.flush()
        edit_version.default_state_id = mismatched_default_state.id
        await session.flush()

        report = await CrossContextConsistencyChecker(session).run(
            ["edit_version_default_state_matches_work_order"]
        )

        assert report.ok is False
        issue = issue_by_name(report, "edit_version_default_state_matches_work_order")
        assert issue.count == 1
        assert issue.sample_rows == [
            {
                "editVersionId": str(edit_version.id),
                "editVersionWorkOrderId": str(edit_version.work_order_id),
                "defaultStateId": str(mismatched_default_state.id),
                "defaultStateWorkOrderId": str(mismatched_work_order_id),
            }
        ]

    run_in_rollback_transaction(scenario)
```

- [ ] **Step 2: Run the integration test without DB flag**

Run:

```powershell
cd apps/backend
pytest tests/integration_tests/test_cross_context_consistency.py -q
```

Expected: SKIPPED with message `Set RUN_DB_TESTS=1 to run PostgreSQL/PostGIS tests.`

- [ ] **Step 3: Run the integration test with a live DB**

Use the existing compose service when it is running:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_cross_context_consistency.py -q
```

Expected: PASS.

---

### Task 4: Smoke Runner And Formatter Tests

**Files:**
- Create: `apps/backend/tests/smoke/cross_context_consistency_smoke.py`
- Create: `apps/backend/tests/smoke/test_cross_context_consistency_smoke.py`
- Test: `apps/backend/tests/smoke/test_cross_context_consistency_smoke.py`

- [ ] **Step 1: Write smoke formatter tests first**

Create `apps/backend/tests/smoke/test_cross_context_consistency_smoke.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from tests.smoke.cross_context_consistency_smoke import exit_code_for_report, format_report
from utility_service.infrastructure.postgresql.consistency import (
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)


def report_with_issues(
    issues: list[CrossContextConsistencyIssue],
) -> CrossContextConsistencyReport:
    error_count = len([issue for issue in issues if issue.severity == "error"])
    return CrossContextConsistencyReport(
        ok=error_count == 0,
        checked_at=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
        checks_run=6,
        error_count=error_count,
        warning_count=len([issue for issue in issues if issue.severity == "warning"]),
        issues=issues,
    )


def test_format_report_outputs_success_summary() -> None:
    report = report_with_issues([])

    assert exit_code_for_report(report) == 0
    assert format_report(report) == "Cross-context consistency: OK\nchecks=6\n"


def test_format_report_outputs_failed_issue_samples() -> None:
    report = report_with_issues(
        [
            CrossContextConsistencyIssue(
                check_name="edit_version_default_state_matches_work_order",
                severity="error",
                message="EditVersion default_state_id указывает на DefaultState другого WorkOrder.",
                source="work_order.edit_versions.default_state_id",
                target="utility_network.default_states.id",
                count=1,
                sample_rows=[
                    {
                        "editVersionId": "edit-version-1",
                        "editVersionWorkOrderId": "work-order-1",
                        "defaultStateId": "default-state-2",
                        "defaultStateWorkOrderId": "work-order-2",
                    }
                ],
            )
        ]
    )

    assert exit_code_for_report(report) == 1
    assert format_report(report) == (
        "Cross-context consistency: FAILED\n"
        "\n"
        "ERROR edit_version_default_state_matches_work_order\n"
        "message: EditVersion default_state_id указывает на DefaultState другого WorkOrder.\n"
        "source: work_order.edit_versions.default_state_id\n"
        "target: utility_network.default_states.id\n"
        "count: 1\n"
        "sample:\n"
        "  editVersionId=edit-version-1 "
        "editVersionWorkOrderId=work-order-1 "
        "defaultStateId=default-state-2 "
        "defaultStateWorkOrderId=work-order-2\n"
    )
```

- [ ] **Step 2: Run the smoke formatter tests to verify they fail**

Run:

```powershell
cd apps/backend
pytest tests/smoke/test_cross_context_consistency_smoke.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `tests.smoke.cross_context_consistency_smoke`.

- [ ] **Step 3: Add the smoke runner**

Create `apps/backend/tests/smoke/cross_context_consistency_smoke.py`:

```python
from __future__ import annotations

import asyncio
import sys
import traceback

from utility_service.infrastructure.postgresql.consistency import (
    CrossContextConsistencyChecker,
    CrossContextConsistencyReport,
)
from utility_service.infrastructure.postgresql.session import SessionFactory


def format_report(report: CrossContextConsistencyReport) -> str:
    if not report.issues:
        return f"Cross-context consistency: OK\nchecks={report.checks_run}\n"

    status = "OK" if report.ok else "FAILED"
    lines = [f"Cross-context consistency: {status}", ""]
    for issue in report.issues:
        lines.extend(
            [
                f"{issue.severity.upper()} {issue.check_name}",
                f"message: {issue.message}",
                f"source: {issue.source}",
                f"target: {issue.target}",
                f"count: {issue.count}",
                "sample:",
            ]
        )
        for sample_row in issue.sample_rows:
            values = " ".join(f"{key}={value}" for key, value in sample_row.items())
            lines.append(f"  {values}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def exit_code_for_report(report: CrossContextConsistencyReport) -> int:
    return 0 if report.ok else 1


async def load_report() -> CrossContextConsistencyReport:
    async with SessionFactory() as session:
        return await CrossContextConsistencyChecker(session).run()


def main() -> int:
    try:
        report = asyncio.run(load_report())
    except Exception:
        print(
            "Cross-context consistency check failed to run. "
            "See traceback for operational context.",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return 1

    stream = sys.stdout if report.ok else sys.stderr
    print(format_report(report), end="", file=stream)
    return exit_code_for_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the smoke formatter tests**

Run:

```powershell
cd apps/backend
pytest tests/smoke/test_cross_context_consistency_smoke.py -q
```

Expected: PASS.

- [ ] **Step 5: Run the live smoke runner inside compose**

Use the existing compose service when it is running:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service python tests/smoke/cross_context_consistency_smoke.py
```

Expected: exit code `0` and output:

```text
Cross-context consistency: OK
checks=6
```

---

### Task 5: CI Wiring

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add the new integration test to the compose DB step**

In `.github/workflows/ci.yml`, locate the step named `PostgreSQL/PostGIS network model tests`.

Add this command after `test_work_order_seed_chain_integration.py` and before `test_utility_network_repository_integration.py`:

```yaml
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_cross_context_consistency.py -q
```

The resulting block must include this sequence:

```yaml
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_cross_context_consistency.py -q
          docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 \
            pytest tests/integration_tests/test_utility_network_repository_integration.py -q
```

- [ ] **Step 2: Validate YAML shape with compose config still available**

Run:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev config --quiet
```

Expected: command exits with code `0`.

---

### Task 6: Focused Verification

**Files:**
- Verify all files from Tasks 1-5.

- [ ] **Step 1: Run fast backend tests for the new non-DB coverage**

Run:

```powershell
cd apps/backend
pytest utility_service/infrastructure/tests/test_cross_context_checker.py tests/smoke/test_cross_context_consistency_smoke.py -q
```

Expected: PASS.

- [ ] **Step 2: Run backend formatting and lint for touched Python files**

Run:

```powershell
cd apps/backend
black --check utility_service/infrastructure/postgresql/consistency utility_service/infrastructure/tests/test_cross_context_checker.py tests/integration_tests/test_cross_context_consistency.py tests/smoke/cross_context_consistency_smoke.py tests/smoke/test_cross_context_consistency_smoke.py
ruff check utility_service/infrastructure/postgresql/consistency utility_service/infrastructure/tests/test_cross_context_checker.py tests/integration_tests/test_cross_context_consistency.py tests/smoke/cross_context_consistency_smoke.py tests/smoke/test_cross_context_consistency_smoke.py
```

Expected: both commands PASS.

- [ ] **Step 3: Run DB integration test inside compose**

Run:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_cross_context_consistency.py -q
```

Expected: PASS.

- [ ] **Step 4: Run live smoke runner inside compose**

Run:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service python tests/smoke/cross_context_consistency_smoke.py
```

Expected:

```text
Cross-context consistency: OK
checks=6
```

- [ ] **Step 5: Run the existing DB CI group if time permits**

Run:

```powershell
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_network_model_integration.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_network_model_migration.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_edit_version_migration.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_seed_utility_dataset_integration.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_cross_context_consistency.py -q
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_utility_network_repository_integration.py -q
```

Expected: all commands PASS.

- [ ] **Step 6: Check whether repository-change ingest is warranted**

Because this implementation adds durable technical knowledge about a new
operational consistency checker, run `/ingest repository-change` after code is
complete if the project owner wants Code_wiki updated in the same task. The
repository-change ingest must write only `Code_wiki` documentation and must not
edit code, migrations, or tests.

Expected: either Code_wiki is updated by repository-change ingest, or the final
answer explicitly says ingest was not run.

---

### Task 7: Final Review Checklist

**Files:**
- Review all changed files.

- [ ] **Step 1: Inspect git diff**

Run:

```powershell
git diff --stat
git diff -- .github/workflows/ci.yml apps/backend/utility_service/infrastructure/postgresql/consistency apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py apps/backend/tests/integration_tests/test_cross_context_consistency.py apps/backend/tests/smoke/cross_context_consistency_smoke.py apps/backend/tests/smoke/test_cross_context_consistency_smoke.py
```

Expected:

- No cross-schema FK additions.
- No Alembic migration changes.
- No service-level HTTP/domain error changes.
- New checker SQL is read-only `select`.
- CI includes `test_cross_context_consistency.py`.

- [ ] **Step 2: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Summarize verification in final handoff**

Final handoff must include:

- New files created.
- CI workflow change.
- Tests run and results.
- Whether live DB/compose checks were run.
- Whether repository-change ingest was run.

Expected: the next reviewer can decide whether to accept the implementation or request changes without re-reading the whole implementation.
