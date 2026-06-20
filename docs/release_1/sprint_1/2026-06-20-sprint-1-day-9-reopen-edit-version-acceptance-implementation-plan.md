# Reopen EditVersion Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend integration/acceptance test proving that repeated opening of a seeded `EditVersion` returns the existing open version without creating duplicate versions or duplicate working-copy rows.

**Architecture:** The change is test-only and belongs in the existing seed-chain integration test file. It exercises the real seed services, `EditVersionService`, repositories, SQLAlchemy models, and PostgreSQL/PostGIS database path already used by CI with `RUN_DB_TESTS=1`. CI already runs the full `test_work_order_seed_chain_integration.py` file, so no workflow change is required.

**Tech Stack:** Python 3.12, pytest, SQLAlchemy async ORM, PostgreSQL/PostGIS, existing `run_in_rollback_transaction` integration-test helper.

---

## Scope Check

This plan implements one acceptance scenario from
`docs/release_1/sprint_1/2026-06-20-sprint-1-day-9-reopen-edit-version-acceptance-design.md`.
It does not change production code, migrations, CI, API routes, seed behavior, or wiki nodes.

Repository rule: do not run `git add` or `git commit` unless the user explicitly asks.

## File Structure

- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
  - Add `EditVersionStatus` to the existing `models.work_order` import.
  - Add one integration test at the end of the file.
  - Reuse existing helpers: `remove_canonical_seed_chain`, `run_seed_chain`, `run_in_rollback_transaction`.

No new files are created.

---

### Task 1: Seed-Chain Reopen Acceptance Test

**Files:**
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Add the missing status enum import**

In `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`, update the existing import from `utility_service.infrastructure.postgresql.models.work_order`.

Replace:

```python
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    WorkOrder,
    WorkOrderStatus,
)
```

With:

```python
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
```

- [ ] **Step 2: Add the failing acceptance test**

Append this test to the end of `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`.

```python
def test_reopening_seeded_edit_version_returns_existing_version_without_duplicates() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        assignee_id = next(
            spec.id
            for spec in SEED_DEMO_USER_SPECS
            if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
        )
        service = EditVersionService(
            session,
            UserRepository(session),
            WorkOrderRepository(session),
            DefaultStateRepository(session),
        )

        first_result = await service.open_for_work_order(
            SEED_WORK_ORDER_SPEC.id,
            assignee_id,
        )
        first_edit_version_id = first_result.edit_version.id
        first_last_opened_at = first_result.edit_version.last_opened_at

        first_open_version_count = await session.scalar(
            select(func.count(EditVersion.id)).where(
                EditVersion.work_order_id == SEED_WORK_ORDER_SPEC.id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        first_edit_feature_count = await session.scalar(
            select(func.count(EditVersionFeature.feature_id)).where(
                EditVersionFeature.edit_version_id == first_edit_version_id
            )
        )
        first_edit_association_count = await session.scalar(
            select(func.count(EditVersionAssociation.association_id)).where(
                EditVersionAssociation.edit_version_id == first_edit_version_id
            )
        )

        second_result = await service.open_for_work_order(
            SEED_WORK_ORDER_SPEC.id,
            assignee_id,
        )

        second_open_version_count = await session.scalar(
            select(func.count(EditVersion.id)).where(
                EditVersion.work_order_id == SEED_WORK_ORDER_SPEC.id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        second_edit_feature_count = await session.scalar(
            select(func.count(EditVersionFeature.feature_id)).where(
                EditVersionFeature.edit_version_id == first_edit_version_id
            )
        )
        second_edit_association_count = await session.scalar(
            select(func.count(EditVersionAssociation.association_id)).where(
                EditVersionAssociation.edit_version_id == first_edit_version_id
            )
        )

        assert first_result.created is True
        assert second_result.created is False
        assert second_result.edit_version.id == first_edit_version_id
        assert first_open_version_count == 1
        assert second_open_version_count == 1
        assert first_edit_feature_count == 19
        assert second_edit_feature_count == 19
        assert first_edit_association_count == 9
        assert second_edit_association_count == 9
        assert second_result.edit_version.last_opened_at >= first_last_opened_at

    run_in_rollback_transaction(scenario)
```

Expected failure before the production code path is correct: the test fails if the second open creates a new version, duplicates working-copy rows, returns `created=True`, returns a different `edit_version.id`, or does not keep exactly one open version.

- [ ] **Step 3: Run the focused test**

From `apps/backend`, run:

```powershell
python -m pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_reopening_seeded_edit_version_returns_existing_version_without_duplicates -q
```

Expected without DB integration environment:

```text
1 skipped
```

Expected with `RUN_DB_TESTS=1` and a configured PostgreSQL/PostGIS `DATABASE_URL`:

```text
1 passed
```

If it fails with `WORK_ORDER_CONTEXT_INVALID`, inspect whether the first open committed the `assigned -> in_progress` transition and whether `get_open_edit_version` can see the created version in the same session.

If it fails with duplicate counts, inspect `WorkOrderRepository.get_open_edit_version`, `create_open_edit_version`, and `touch_edit_version`; do not weaken the acceptance assertions.

- [ ] **Step 4: Run the full seed-chain integration file**

From `apps/backend`, run:

```powershell
python -m pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected without DB integration environment:

```text
4 skipped
```

Expected with `RUN_DB_TESTS=1` and a configured PostgreSQL/PostGIS `DATABASE_URL`:

```text
4 passed
```

- [ ] **Step 5: Run the related service and integration coverage**

From `apps/backend`, run:

```powershell
python -m pytest utility_service/use_cases/tests/test_edit_version_service.py tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected without DB integration environment:

```text
8 passed, 4 skipped
```

Expected with `RUN_DB_TESTS=1` and a configured PostgreSQL/PostGIS `DATABASE_URL`:

```text
12 passed
```

- [ ] **Step 6: Confirm CI coverage does not need a workflow edit**

From repository root, run:

```powershell
rg -n "test_work_order_seed_chain_integration.py" .github\workflows\ci.yml
```

Expected output includes:

```text
.github\workflows\ci.yml:138:            pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

No CI file edit is required because the new test lives in a file already executed by the PostgreSQL/PostGIS CI job with `RUN_DB_TESTS=1`.

- [ ] **Step 7: Record the working tree state**

From repository root, run:

```powershell
git status --short
```

Expected: the implementation changes include only:

```text
 M apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py
```

There may already be unrelated working-tree changes. Do not revert, stage, or commit them.

## Self-Review Checklist

- The plan covers every acceptance criterion in the design spec.
- The new test uses the real seed chain, real repositories, real service, and real database helper.
- The plan does not modify production code, migrations, CI, or wiki nodes.
- `EditVersionStatus` is imported from `utility_service.infrastructure.postgresql.models.work_order`.
- The expected CI behavior is explicit: the file is already run in `.github/workflows/ci.yml`.
- No deferred implementation notes remain.
