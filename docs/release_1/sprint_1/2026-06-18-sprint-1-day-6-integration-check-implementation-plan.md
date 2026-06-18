# Sprint 1 Day 6 Integration Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not create a git commit unless the user explicitly asks for it after review.

**Goal:** Verify the existing Sprint 1 backend chain from migrations through demo users, utility dataset, and work order seed without adding public Work Orders API, frontend, `EditVersion`, or workspace behavior.

**Architecture:** Add a focused PostgreSQL/PostGIS integration test around the existing seed services and models. Fix only the startup orchestration script if it does not run `seed_work_orders` after `seed_utility_dataset`. Keep business rules in existing seed/use-case services and keep the integration day as a thin verification layer.

**Tech Stack:** Python, pytest, SQLAlchemy async ORM, Alembic, PostgreSQL/PostGIS, existing `seeds` package, existing shell startup script.

---

## File Structure

- Create: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py` - DB integration smoke for `demo users -> utility dataset -> work orders` and idempotency.
- Modify: `apps/backend/scripts/start_utility_service.sh` - include `python -m seeds.runners.seed_work_orders` between utility dataset seed and `uvicorn`.
- Existing Test: `apps/backend/tests/test_compose_startup_contract.py` - already asserts all seed runners are ordered before API startup.
- Modify: `docs/release_1/sprint_1/README.md` - add the Day 6 implementation plan link after the Day 6 design link.

## Task 1: Startup Script Seed Chain

**Files:**
- Modify: `apps/backend/scripts/start_utility_service.sh`
- Existing Test: `apps/backend/tests/test_compose_startup_contract.py`

- [ ] **Step 1: Run existing startup contract red**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_startup_contract.py -q
```

Expected: FAIL with a missing substring or `ValueError` for:

```text
python -m seeds.runners.seed_work_orders
```

- [ ] **Step 2: Add work order seed runner to startup script**

Change `apps/backend/scripts/start_utility_service.sh` to this exact seed order:

```bash
#!/usr/bin/env bash
set -e
alembic upgrade head
python -m seeds.runners.seed_demo_users
python -m seeds.runners.seed_utility_dataset
python -m seeds.runners.seed_work_orders

uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
```

Do not add Work Orders API routes, frontend code, `EditVersion`, or reset/full-clean behavior.

- [ ] **Step 3: Run startup contract green**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_startup_contract.py -q
```

Expected: PASS. The test confirms all three seed runners run before:

```text
uvicorn utility_service.web_api.main:app
```

## Task 2: Work Order Seed Chain Integration Test

**Files:**
- Create: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Write integration smoke test**

Create `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py` with this content:

```python
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.services.seed_work_order_service import SeedWorkOrderService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC
from tests.integration_tests.network_db_support import run_in_rollback_transaction
from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
    WorkOrder,
    WorkOrderStatus,
)


async def remove_canonical_seed_chain(session: AsyncSession) -> None:
    await session.execute(
        delete(WorkOrder).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
    )
    await session.execute(
        delete(NetworkAssociation).where(
            NetworkAssociation.feeder_id == UTILITY_DATASET_SPEC.feeder.id
        )
    )
    await session.execute(
        delete(NetworkFeature).where(
            NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id
        )
    )
    await session.execute(delete(Feeder).where(Feeder.id == UTILITY_DATASET_SPEC.feeder.id))
    await session.execute(delete(AOI).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id))
    await session.execute(
        delete(User).where(
            User.email.in_([spec.email for spec in SEED_DEMO_USER_SPECS])
        )
    )
    await session.commit()


async def run_seed_chain(session: AsyncSession) -> None:
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


async def load_work_order(session: AsyncSession) -> WorkOrder:
    work_order = await session.scalar(
        select(WorkOrder).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
    )
    assert work_order is not None
    return work_order


def test_seed_chain_creates_work_order_with_user_network_links() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)

        await run_seed_chain(session)

        work_order = await load_work_order(session)
        assignee = await session.get(User, work_order.assignee_id)
        feeder = await session.get(Feeder, work_order.feeder_id)
        aoi = await session.get(AOI, work_order.aoi_id)
        reviewer = await session.scalar(
            select(User).where(User.email == "marina.reviewer@example.local")
        )
        work_order_count = await session.scalar(
            select(func.count(WorkOrder.id)).where(
                WorkOrder.code == SEED_WORK_ORDER_SPEC.code
            )
        )
        network_feature_count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id
            )
        )

        assert work_order_count == 1
        assert work_order.id == SEED_WORK_ORDER_SPEC.id
        assert work_order.status is WorkOrderStatus.ASSIGNED
        assert assignee is not None
        assert assignee.email == SEED_WORK_ORDER_SPEC.assignee_email
        assert assignee.role is UserRole.EDITOR
        assert assignee.is_active is True
        assert reviewer is not None
        assert reviewer.role is UserRole.REVIEWER
        assert reviewer.id != work_order.assignee_id
        assert feeder is not None
        assert feeder.code == UTILITY_FEEDER_CODE
        assert aoi is not None
        assert network_feature_count == 19

    run_in_rollback_transaction(scenario)


def test_repeated_seed_chain_preserves_existing_work_order_state() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        work_order = await load_work_order(session)
        work_order.title = "Измененная задача интеграционного дня"
        work_order.status = WorkOrderStatus.IN_PROGRESS
        original_assignee_id = work_order.assignee_id
        original_aoi_id = work_order.aoi_id
        original_feeder_id = work_order.feeder_id
        await session.commit()

        await run_seed_chain(session)

        refreshed = await load_work_order(session)
        work_order_count = await session.scalar(
            select(func.count(WorkOrder.id)).where(
                WorkOrder.code == SEED_WORK_ORDER_SPEC.code
            )
        )

        assert work_order_count == 1
        assert refreshed.title == "Измененная задача интеграционного дня"
        assert refreshed.status is WorkOrderStatus.IN_PROGRESS
        assert refreshed.assignee_id == original_assignee_id
        assert refreshed.aoi_id == original_aoi_id
        assert refreshed.feeder_id == original_feeder_id

    run_in_rollback_transaction(scenario)
```

- [ ] **Step 2: Run new integration test if database tests are available**

Run from `apps/backend` with a PostgreSQL/PostGIS test database configured:

```powershell
$env:RUN_DB_TESTS='1'; pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected after Task 1 implementation and current migrations: PASS. If the local test database is behind, expected: FAIL with a migration/schema or seed dependency error that should be fixed before continuing. If `RUN_DB_TESTS` is not set, expected result is SKIPPED by `network_db_support.require_db_tests()`.

- [ ] **Step 3: Keep implementation minimal**

No extra production code is needed for this task if Task 1 already added the startup script seed runner and existing seed services work. Do not edit:

```text
utility_service/web_api/api/*.py
utility_service/web_api/main.py
utility_service/infrastructure/postgresql/models/utility_network/*.py
```

The integration test should exercise existing services:

```python
SeedDemoUserService
SeedUtilityDatasetService
SeedWorkOrderService
```

- [ ] **Step 4: Run new integration test green if database tests are available**

Run from `apps/backend`:

```powershell
$env:RUN_DB_TESTS='1'; pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: PASS with 2 tests when PostgreSQL/PostGIS is available. If DB tests are disabled, expected: SKIPPED.

## Task 3: Sprint Documentation Link

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`

- [ ] **Step 1: Add implementation plan link to sprint README**

Add this line immediately after the Day 6 design link:

```markdown
- [План реализации облегченной интеграционной проверки Дня 6](2026-06-18-sprint-1-day-6-integration-check-implementation-plan.md)
```

The surrounding block should contain both Day 6 links:

```markdown
- [Облегченная интеграционная проверка Дня 6](2026-06-18-sprint-1-day-6-integration-check-design.md)
- [План реализации облегченной интеграционной проверки Дня 6](2026-06-18-sprint-1-day-6-integration-check-implementation-plan.md)
```

- [ ] **Step 2: Verify README link target exists**

Run from repo root:

```powershell
Test-Path docs\release_1\sprint_1\2026-06-18-sprint-1-day-6-integration-check-implementation-plan.md
```

Expected:

```text
True
```

## Task 4: Verification

**Files:**
- No additional file edits.

- [ ] **Step 1: Run targeted unit and contract suite**

Run from `apps/backend`:

```powershell
pytest tests/test_compose_startup_contract.py seeds/tests/test_seed_work_order_specs.py seeds/tests/test_seed_work_order_service.py utility_service/use_cases/tests/test_work_order_service.py utility_service/infrastructure/tests/test_network_model_metadata.py -q
```

Expected: PASS.

- [ ] **Step 2: Run Day 4/5 related regression tests**

Run from `apps/backend`:

```powershell
pytest seeds/tests/test_seed_utility_dataset_specs.py seeds/tests/test_seed_utility_dataset_service.py utility_service/use_cases/tests/test_utility_network_service.py utility_service/web_api/tests/test_utility_network_api.py -q
```

Expected: PASS.

- [ ] **Step 3: Run DB integration smoke when PostgreSQL/PostGIS is available**

Run from `apps/backend` with `DATABASE_URL` pointing to the test database:

```powershell
$env:RUN_DB_TESTS='1'; pytest tests/integration_tests/test_work_order_seed_chain_integration.py tests/integration_tests/test_seed_utility_dataset_integration.py -q
```

Expected: PASS. If the local machine has no configured PostgreSQL/PostGIS test database, do not fake the result; report that DB integration tests were not run.

- [ ] **Step 4: Search for forbidden scope creep**

Run from repo root:

```powershell
rg -n "work-orders|EditVersion|My Work Orders|reviewer queue|approve|reject|post" apps\frontend apps\backend\utility_service\web_api docs\release_1\sprint_1\2026-06-18-sprint-1-day-6-integration-check-implementation-plan.md
```

Expected: matches are limited to documentation text or existing files; no new Work Orders public API, frontend, `EditVersion`, reviewer workflow, or post behavior is introduced by Day 6 implementation.

- [ ] **Step 5: Run memory-needed check only if operating docs or agent memory changed**

Run from repo root if implementation touched `docs/agent-memory/`, `.agents/`, `AGENTS.md`, or knowledge-pipeline operating docs:

```powershell
python scripts/check-memory-needed.py --check
```

Expected: `Memory update check passed.` If only sprint docs and backend code changed, do not create agent memory for task completion or test logs.

## Self-Review

- Spec coverage: Tasks 1-2 cover migration/startup/seed chain and `WorkOrder -> User/AOI/Feeder` invariants. Task 2 covers idempotency and Reviewer-not-assignee. Task 4 covers targeted verification and scope boundaries.
- Text scan: no unresolved draft markers, vague test instructions, or unnamed files remain.
- Type consistency: test code uses existing `SeedDemoUserService`, `SeedUtilityDatasetService`, `SeedWorkOrderService`, `SEED_WORK_ORDER_SPEC`, `UTILITY_DATASET_SPEC`, `UTILITY_FEEDER_CODE`, `WorkOrderStatus`, `UserRole`, and existing `run_in_rollback_transaction`.
- Scope check: plan does not add public Work Orders API, frontend, `EditVersion`, workspace API, reset/full-clean, reviewer queue, approve/reject, or post.
