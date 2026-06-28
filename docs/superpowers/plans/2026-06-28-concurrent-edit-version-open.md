# Concurrent Open EditVersion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать `POST /api/v1/work-orders/{workOrderId}/edit-versions` идемпотентным при конкурентном открытии одного `WorkOrder`: один запрос создает `EditVersion` и получает `201`, остальные возвращают ту же версию как reopen с `200`.

**Architecture:** Основной путь берет row-level lock на `WorkOrder` через `SELECT ... FOR UPDATE`, затем выполняет существующую логику create/reopen под этой блокировкой. Partial unique index `uq_edit_versions_open_work_order` остается DB-инвариантом, а constraint-specific `IntegrityError` recovery перечитывает existing open version в новой транзакции.

**Tech Stack:** Python 3.12, SQLAlchemy 2 async ORM, PostgreSQL/PostGIS, FastAPI, pytest, Docker dev image `utility_service:dev`.

**Git Rule:** План намеренно не содержит операций записи в Git. Фиксацию изменений выполняет пользователь после проверки.

---

## Source Spec

- `docs/superpowers/specs/2026-06-28-concurrent-edit-version-open-design.md`
- Review finding: `docs/release_1/sprint_1/2026-06-28-sprint-1-deep-code-review.md`, section `P1. Гонка при idempotent open EditVersion может превратиться в 500`

## File Structure

- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
  - Responsibility: database access for `WorkOrder`, including the new locked read used by open `EditVersion`.
- Modify: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository.py`
  - Responsibility: repository SQL shape tests, including `FOR UPDATE`.
- Modify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`
  - Responsibility: domain/use-case orchestration for open/reopen `EditVersion`, row-lock flow, and `IntegrityError` recovery.
- Modify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
  - Responsibility: fast unit coverage for locked read, idempotent reopen, and constraint-specific recovery.
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
  - Responsibility: PostgreSQL/PostGIS integration coverage for seeded work-order chain and concurrent open behavior.

No API schema, frontend file, Alembic migration, or database model change is required.

---

### Task 1: Add Repository Row Lock

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`

- [x] **Step 1: Write the failing repository SQL test**

In `apps/backend/utility_service/infrastructure/tests/test_work_order_repository.py`, add the PostgreSQL dialect import and extend the fake scalar result so `get_by_id_for_update()` can call `one_or_none()`:

```python
from sqlalchemy.dialects import postgresql
```

```python
class _ScalarResult:
    def all(self):
        return []

    def one_or_none(self):
        return None
```

Add this test after `test_list_assigned_to_user_orders_by_updated_at_desc_then_code`:

```python
def test_get_by_id_for_update_locks_work_order_row() -> None:
    session = CapturingSession()
    repository = WorkOrderRepository(session)
    work_order_id = uuid4()

    result = asyncio.run(repository.get_by_id_for_update(work_order_id))

    assert result is None
    assert session.statement is not None
    compiled = str(
        session.statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )
    assert "FROM work_order.work_orders" in compiled
    assert "work_order.work_orders.id" in compiled
    assert "FOR UPDATE" in compiled
```

- [x] **Step 2: Run the new repository test and verify it fails**

Run from `C:\Repositories\geoservice`:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository.py::test_get_by_id_for_update_locks_work_order_row -q"
```

Expected: FAIL with `AttributeError: 'WorkOrderRepository' object has no attribute 'get_by_id_for_update'`.

- [x] **Step 3: Implement the locked repository read**

In `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`, add this method immediately after `get_by_id()`:

```python
    async def get_by_id_for_update(self, work_order_id: UUID) -> WorkOrder | None:
        result = await self.session.execute(
            select(WorkOrder).where(WorkOrder.id == work_order_id).with_for_update()
        )
        return result.scalars().one_or_none()
```

- [x] **Step 4: Run the repository tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository.py -q"
```

Expected: PASS for both repository tests.

---

### Task 2: Use Locked Read In EditVersionService

**Files:**
- Modify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`

- [x] **Step 1: Write the failing use-case test for locked read**

In `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`, update `build_service()` so the default fake repository exposes `get_by_id_for_update`:

```python
        work_order_repository=work_order_repository
        or repository(
            get_by_id=None,
            get_by_id_for_update=None,
            get_open_edit_version=None,
            create_open_edit_version=None,
            touch_edit_version=None,
            save=None,
        ),
```

Add this test after `test_open_assigned_work_order_creates_edit_version_and_starts_work_order`:

```python
def test_open_reads_work_order_with_row_lock() -> None:
    actor = user()
    assigned = work_order(actor.id)
    created = edit_version(assigned.id, actor.id)
    baseline = default_state(assigned.id, base_network_revision=12)
    baseline_aggregate = SimpleNamespace(
        state=baseline,
        features=[default_feature(baseline.id)],
        associations=[default_association(baseline.id)],
    )
    work_order_repository = repository(
        get_by_id=assigned,
        get_by_id_for_update=assigned,
        get_open_edit_version=None,
        create_open_edit_version=created,
        touch_edit_version=None,
        save=None,
    )
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=work_order_repository,
        default_state_repository=repository(
            get_active_aggregate_by_work_order_id=baseline_aggregate,
        ),
    )

    result = asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert result.created is True
    work_order_repository.get_by_id_for_update.assert_awaited_once_with(assigned.id)
    work_order_repository.get_by_id.assert_not_awaited()
```

- [x] **Step 2: Run the new use-case test and verify it fails**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py::test_open_reads_work_order_with_row_lock -q"
```

Expected: FAIL because `get_by_id_for_update` was not awaited and ordinary `get_by_id` was awaited.

- [x] **Step 3: Change service visibility lookup to use the locked method**

In `apps/backend/utility_service/use_cases/services/edit_version_service.py`, replace the body of `get_visible_work_order()` with:

```python
    async def get_visible_work_order(self, work_order_id: UUID, actor: User) -> WorkOrder:
        work_order = await self.work_order_repository.get_by_id_for_update(work_order_id)
        if work_order is None or work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        return work_order
```

- [x] **Step 4: Update existing service tests to provide the locked method**

In `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`, update existing fake repositories so the service can call `get_by_id_for_update`.

For tests where the work order exists, use this pattern:

```python
    work_order_repository = repository(
        get_by_id_for_update=assigned,
        get_open_edit_version=None,
        create_open_edit_version=created,
        touch_edit_version=None,
        save=None,
    )
```

For the in-progress reopen test, use:

```python
    work_order_repository = repository(
        get_by_id_for_update=started,
        get_open_edit_version=existing,
        create_open_edit_version=None,
        touch_edit_version=None,
        save=None,
    )
```

For wrong-assignee and corrupted-context tests, replace `get_by_id=...` with `get_by_id_for_update=...`.

For `test_open_rejects_non_active_editor`, use this repository fake and assertion:

```python
    work_order_repository = repository(get_by_id_for_update=None, save=None)
```

```python
    work_order_repository.get_by_id_for_update.assert_not_awaited()
```

- [x] **Step 5: Run all EditVersionService unit tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py -q"
```

Expected: PASS.

---

### Task 3: Add Constraint-Specific IntegrityError Classifier

**Files:**
- Modify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`

- [x] **Step 1: Write classifier tests**

In `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`, add the import:

```python
from sqlalchemy.exc import IntegrityError
```

Add these helpers near `FakeSession`:

```python
class _FakeIntegrityDiag:
    def __init__(self, constraint_name: str | None) -> None:
        self.constraint_name = constraint_name


class _FakeIntegrityOriginal:
    def __init__(
        self,
        *,
        sqlstate: str = "23505",
        constraint_name: str | None = "uq_edit_versions_open_work_order",
    ) -> None:
        self.sqlstate = sqlstate
        self.pgcode = sqlstate
        self.diag = _FakeIntegrityDiag(constraint_name)
        self.constraint_name = constraint_name


def integrity_error(
    *,
    sqlstate: str = "23505",
    constraint_name: str | None = "uq_edit_versions_open_work_order",
) -> IntegrityError:
    return IntegrityError(
        "insert failed",
        {},
        _FakeIntegrityOriginal(sqlstate=sqlstate, constraint_name=constraint_name),
    )
```

Add these tests after `build_service()`:

```python
def test_open_edit_version_unique_violation_matches_constraint() -> None:
    error = integrity_error()

    assert EditVersionService.is_open_edit_version_unique_violation(error) is True


def test_open_edit_version_unique_violation_rejects_other_constraint() -> None:
    error = integrity_error(constraint_name="uq_edit_version_features_edit_version_asset_code")

    assert EditVersionService.is_open_edit_version_unique_violation(error) is False


def test_open_edit_version_unique_violation_rejects_other_sqlstate() -> None:
    error = integrity_error(sqlstate="23503", constraint_name="uq_edit_versions_open_work_order")

    assert EditVersionService.is_open_edit_version_unique_violation(error) is False
```

- [x] **Step 2: Run classifier tests and verify they fail**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_matches_constraint utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_rejects_other_constraint utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_rejects_other_sqlstate -q"
```

Expected: FAIL because `EditVersionService.is_open_edit_version_unique_violation` does not exist.

- [x] **Step 3: Implement the classifier**

In `apps/backend/utility_service/use_cases/services/edit_version_service.py`, add the import:

```python
from sqlalchemy.exc import IntegrityError
```

Add these constants near `OpenEditVersionResult`:

```python
OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT = "uq_edit_versions_open_work_order"
POSTGRES_UNIQUE_VIOLATION = "23505"
```

Add this static method inside `EditVersionService`, near the bottom before `raise_context_invalid()`:

```python
    @staticmethod
    def is_open_edit_version_unique_violation(error: IntegrityError) -> bool:
        original = getattr(error, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diag = getattr(original, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None) or getattr(
            original,
            "constraint_name",
            None,
        )
        return sqlstate == POSTGRES_UNIQUE_VIOLATION and (
            constraint_name == OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT
            or OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT in str(error)
        )
```

- [x] **Step 4: Run classifier tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_matches_constraint utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_rejects_other_constraint utility_service/use_cases/tests/test_edit_version_service.py::test_open_edit_version_unique_violation_rejects_other_sqlstate -q"
```

Expected: PASS.

---

### Task 4: Recover Concurrent Open After Unique Violation

**Files:**
- Modify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`

- [x] **Step 1: Write recovery and propagation tests**

In `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`, add these tests after `test_open_in_progress_work_order_returns_existing_edit_version`:

```python
def test_open_recovers_unique_violation_as_existing_edit_version() -> None:
    actor = user()
    assigned = work_order(actor.id)
    started = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    started.id = assigned.id
    existing = edit_version(assigned.id, actor.id)
    baseline = default_state(assigned.id, base_network_revision=12)
    baseline_aggregate = SimpleNamespace(
        state=baseline,
        features=[default_feature(baseline.id)],
        associations=[default_association(baseline.id)],
    )
    session = FakeSession()
    work_order_repository = repository(
        get_by_id_for_update=None,
        get_open_edit_version=None,
        create_open_edit_version=None,
        touch_edit_version=None,
        save=None,
    )
    work_order_repository.get_by_id_for_update.side_effect = [assigned, started]
    work_order_repository.get_open_edit_version.side_effect = [None, existing]
    work_order_repository.create_open_edit_version.side_effect = integrity_error()
    service = build_service(
        session=session,
        user_repository=repository(get_by_id=actor),
        work_order_repository=work_order_repository,
        default_state_repository=repository(
            get_active_aggregate_by_work_order_id=baseline_aggregate,
        ),
    )

    result = asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert result.created is False
    assert result.edit_version is existing
    assert session.begin_calls == 2
    assert work_order_repository.get_by_id_for_update.await_count == 2
    assert work_order_repository.get_open_edit_version.await_count == 2
    work_order_repository.touch_edit_version.assert_awaited_once_with(existing)
    work_order_repository.save.assert_not_awaited()


def test_open_does_not_recover_other_integrity_error() -> None:
    actor = user()
    assigned = work_order(actor.id)
    baseline = default_state(assigned.id, base_network_revision=12)
    baseline_aggregate = SimpleNamespace(
        state=baseline,
        features=[default_feature(baseline.id)],
        associations=[default_association(baseline.id)],
    )
    session = FakeSession()
    work_order_repository = repository(
        get_by_id_for_update=assigned,
        get_open_edit_version=None,
        create_open_edit_version=None,
        touch_edit_version=None,
        save=None,
    )
    work_order_repository.create_open_edit_version.side_effect = integrity_error(
        constraint_name="uq_edit_version_features_edit_version_asset_code",
    )
    service = build_service(
        session=session,
        user_repository=repository(get_by_id=actor),
        work_order_repository=work_order_repository,
        default_state_repository=repository(
            get_active_aggregate_by_work_order_id=baseline_aggregate,
        ),
    )

    with pytest.raises(IntegrityError):
        asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert session.begin_calls == 1
    work_order_repository.touch_edit_version.assert_not_awaited()
```

- [x] **Step 2: Run recovery tests and verify they fail**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py::test_open_recovers_unique_violation_as_existing_edit_version utility_service/use_cases/tests/test_edit_version_service.py::test_open_does_not_recover_other_integrity_error -q"
```

Expected: first test FAILS because `IntegrityError` is not recovered. The second test may already pass; keep it as regression coverage.

- [x] **Step 3: Refactor service into locked path and recovery path**

In `apps/backend/utility_service/use_cases/services/edit_version_service.py`, replace `open_for_work_order()` with:

```python
    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        try:
            return await self.open_for_work_order_locked(work_order_id, actor_id)
        except IntegrityError as exc:
            if not self.is_open_edit_version_unique_violation(exc):
                raise
            return await self.recover_existing_open_edit_version(work_order_id, actor_id)
```

Add these methods below `open_for_work_order()`:

```python
    async def open_for_work_order_locked(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            return await self.open_visible_work_order(work_order, actor)

    async def open_visible_work_order(
        self,
        work_order: WorkOrder,
        actor: User,
    ) -> OpenEditVersionResult:
        existing = await self.work_order_repository.get_open_edit_version(work_order.id)

        if work_order.status is WorkOrderStatus.IN_PROGRESS:
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

        if work_order.status is not WorkOrderStatus.ASSIGNED:
            raise WorkOrderApiError(
                409,
                "WORK_ORDER_STATE_CONFLICT",
                "Состояние рабочей задачи не допускает операцию.",
            )

        if existing is not None:
            self.raise_context_invalid()

        default_state_aggregate = (
            await self.default_state_repository.get_active_aggregate_by_work_order_id(
                work_order.id
            )
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

    async def recover_existing_open_edit_version(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            existing = await self.work_order_repository.get_open_edit_version(work_order.id)
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

    async def reopen_edit_version(self, edit_version: EditVersion) -> OpenEditVersionResult:
        await self.work_order_repository.touch_edit_version(edit_version)
        return OpenEditVersionResult(created=False, edit_version=edit_version)
```

Keep `get_actor()`, `get_visible_work_order()`, `require_active_editor()`, `is_open_edit_version_unique_violation()`, and `raise_context_invalid()` after these methods.

- [x] **Step 4: Run all EditVersionService unit tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_edit_version_service.py -q"
```

Expected: PASS.

---

### Task 5: Add PostgreSQL Concurrent Open Regression Test

**Files:**
- Modify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [x] **Step 1: Write the DB-gated concurrent open test**

In `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`, add imports at the top:

```python
import asyncio
import os
```

Change the SQLAlchemy async import to:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
```

Change the support import to:

```python
from tests.integration_tests.network_db_support import (
    require_db_tests,
    run_in_rollback_transaction,
)
```

Add this test after `test_reopening_seeded_edit_version_returns_existing_version_without_duplicates`:

```python
def test_concurrent_open_seeded_edit_version_returns_one_created_and_one_reopened() -> None:
    require_db_tests()

    async def assert_demo_users_restored() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        Session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        try:
            async with Session() as session:
                emails = (await session.execute(select(User.email))).scalars().all()
        finally:
            await engine.dispose()

        assert set(emails) == {spec.email for spec in SEED_DEMO_USER_SPECS}

    async def scenario() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        Session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        try:
            async with Session() as setup_session:
                await remove_canonical_seed_chain(setup_session)
                await run_seed_chain(setup_session)

            assignee_id = next(
                spec.id
                for spec in SEED_DEMO_USER_SPECS
                if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
            )

            async def open_once():
                async with Session() as session:
                    return await EditVersionService(
                        session,
                        UserRepository(session),
                        WorkOrderRepository(session),
                        DefaultStateRepository(session),
                    ).open_for_work_order(SEED_WORK_ORDER_SPEC.id, assignee_id)

            first_result, second_result = await asyncio.gather(open_once(), open_once())
            created_flags = sorted([first_result.created, second_result.created])
            edit_version_ids = {first_result.edit_version.id, second_result.edit_version.id}
            edit_version_id = next(iter(edit_version_ids))

            async with Session() as verify_session:
                open_version_count = await verify_session.scalar(
                    select(func.count(EditVersion.id)).where(
                        EditVersion.work_order_id == SEED_WORK_ORDER_SPEC.id,
                        EditVersion.status == EditVersionStatus.OPEN,
                    )
                )
                edit_feature_count = await verify_session.scalar(
                    select(func.count(EditVersionFeature.feature_id)).where(
                        EditVersionFeature.edit_version_id == edit_version_id
                    )
                )
                edit_association_count = await verify_session.scalar(
                    select(func.count(EditVersionAssociation.association_id)).where(
                        EditVersionAssociation.edit_version_id == edit_version_id
                    )
                )
                work_order_status = await verify_session.scalar(
                    select(WorkOrder.status).where(WorkOrder.id == SEED_WORK_ORDER_SPEC.id)
                )

            assert created_flags == [False, True]
            assert len(edit_version_ids) == 1
            assert open_version_count == 1
            assert edit_feature_count == 19
            assert edit_association_count == 9
            assert work_order_status is WorkOrderStatus.IN_PROGRESS
        finally:
            try:
                async with Session() as cleanup_session:
                    await remove_canonical_seed_chain(cleanup_session)
                    await run_seed_chain(cleanup_session)
            finally:
                await engine.dispose()

    asyncio.run(scenario())
    asyncio.run(assert_demo_users_restored())
```

- [x] **Step 2: Run the integration test**

Run from `C:\Repositories\geoservice\infra` with the compose stack already running:

```powershell
docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_concurrent_open_seeded_edit_version_returns_one_created_and_one_reopened -q
```

Expected: PASS. If it fails with a real race defect, inspect the assertion output before changing the test.

- [x] **Step 3: Run the full work-order seed-chain integration file**

Run from `C:\Repositories\geoservice\infra`:

```powershell
docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: PASS.

---

### Task 6: Final Backend Verification

**Files:**
- Verify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
- Verify: `apps/backend/utility_service/infrastructure/tests/test_work_order_repository.py`
- Verify: `apps/backend/utility_service/use_cases/services/edit_version_service.py`
- Verify: `apps/backend/utility_service/use_cases/tests/test_edit_version_service.py`
- Verify: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [x] **Step 1: Run focused fast unit tests**

Run from `C:\Repositories\geoservice`:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/infrastructure/tests/test_work_order_repository.py utility_service/use_cases/tests/test_edit_version_service.py -q"
```

Expected: PASS.

- [x] **Step 2: Run backend formatting check**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black --check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository.py utility_service/use_cases/services/edit_version_service.py utility_service/use_cases/tests/test_edit_version_service.py tests/integration_tests/test_work_order_seed_chain_integration.py"
```

Expected: PASS with all listed files left unchanged.

- [x] **Step 3: Run backend lint on changed files**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "ruff check utility_service/infrastructure/postgresql/repositories/work_order_repository.py utility_service/infrastructure/tests/test_work_order_repository.py utility_service/use_cases/services/edit_version_service.py utility_service/use_cases/tests/test_edit_version_service.py tests/integration_tests/test_work_order_seed_chain_integration.py"
```

Expected: PASS with `All checks passed!`.

- [x] **Step 4: Run full backend unit test suite**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest"
```

Expected: PASS. Integration tests without `RUN_DB_TESTS=1` should skip as they do today.

- [x] **Step 5: Run DB integration regression in compose**

Run from `C:\Repositories\geoservice\infra`:

```powershell
docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: PASS, including `test_concurrent_open_seeded_edit_version_returns_one_created_and_one_reopened`.

- [x] **Step 6: Inspect diff**

Run:

```powershell
git diff -- apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py apps/backend/utility_service/infrastructure/tests/test_work_order_repository.py apps/backend/utility_service/use_cases/services/edit_version_service.py apps/backend/utility_service/use_cases/tests/test_edit_version_service.py apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py
```

Expected: diff only contains the row-lock repository method, use-case recovery logic, and tests described in this plan.

- [x] **Step 7: Decide whether knowledge docs need update**

Решение: `/ingest repository-change` не нужен; поведение SQLAlchemy/asyncpg
при recovery и риск cleanup seed-состояния в CI уже закреплены кодом, тестами
и этим планом.

Do not run `/ingest repository-change` automatically. Decide after implementation:

- If the final code only implements this spec and no new durable technical pattern appears beyond the written design, do not update `Code_wiki`.
- If implementation reveals a non-obvious SQLAlchemy/asyncpg recovery constraint that future agents must know, update an existing relevant `Code_wiki` node through `/ingest repository-change`.

---

## Self-Review

- Spec coverage: row lock is covered in Task 1 and Task 2; unique-index recovery is covered in Task 3 and Task 4; concurrent DB behavior is covered in Task 5; final regression gates are covered in Task 6.
- API scope: no task changes FastAPI route, DTOs, frontend, database schema, or migrations.
- Error handling: classifier limits recovery to SQLSTATE `23505` and `uq_edit_versions_open_work_order`; other `IntegrityError` cases remain visible.
- Test path: fast unit tests prove repository SQL and recovery; DB integration proves two independent sessions return one created and one reopened version.
- Type consistency: planned method names are `get_by_id_for_update`, `open_for_work_order_locked`, `open_visible_work_order`, `recover_existing_open_edit_version`, `reopen_edit_version`, and `is_open_edit_version_unique_violation`.
- Git operations: plan intentionally contains no Git write steps; user handles change recording after review.
