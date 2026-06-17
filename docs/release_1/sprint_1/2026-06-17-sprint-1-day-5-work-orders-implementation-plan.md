# Sprint 1 Day 5 Work Orders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build backend foundation for `WorkOrder`: model, status, assignment, create-once seed, service checks, and unit-test coverage.

**Architecture:** `WorkOrder` lives in the existing `utility_network` schema and follows the current `utility_service` package boundaries. SQLAlchemy models and repositories stay in `infrastructure/postgresql`, business checks live in `use_cases`, and demo data lives in `seeds`. No HTTP endpoint, frontend, `EditVersion`, integration-test gate, or public workspace behavior is added in this plan.

**Tech Stack:** Python, SQLAlchemy async ORM, Alembic, pytest, FastAPI-adjacent use-case services, PostgreSQL/PostGIS schema conventions.

---

## File Structure

- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py` - `WorkOrderStatus` enum and `WorkOrder` ORM model.
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py` - export `WorkOrder` and `WorkOrderStatus`.
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py` - import `WorkOrder` for autogenerate metadata.
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/e4b7a9c2d5f8_work_orders.py` - migration for `utility_network.work_orders`.
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py` - thin async repository.
- Create: `apps/backend/utility_service/use_cases/domain/exceptions/work_order_api_error.py` - structured work-order use-case error.
- Create: `apps/backend/utility_service/use_cases/services/work_order_service.py` - `actor_id` loading, assignment and status business rules.
- Modify: `apps/backend/utility_service/use_cases/deps.py` - add future-ready `get_work_order_service` factory without wiring a route.
- Create: `apps/backend/seeds/specs/seed_work_order_specs.py` - stable `WO-001` spec.
- Create: `apps/backend/seeds/repositories/seed_work_order_repository.py` - seed-only reads and create method.
- Create: `apps/backend/seeds/services/seed_work_order_service.py` - create-once seed service.
- Create: `apps/backend/seeds/runners/seed_work_orders.py` - optional module runner.
- Modify: `apps/backend/utility_service/web_api/api/lifespan.py` - no startup seed change in this implementation unless existing startup already invokes seed runners. Day 5 keeps API behavior unchanged.
- Test: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py` - metadata/export tests for `WorkOrder`.
- Test: `apps/backend/seeds/tests/test_seed_work_order_specs.py` - stable spec tests.
- Test: `apps/backend/seeds/tests/test_seed_work_order_service.py` - create-once seed behavior tests.
- Test: `apps/backend/utility_service/use_cases/tests/test_work_order_service.py` - assignment and state transition tests.

## Task 1: Model Metadata

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/__init__.py`
- Modify: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/e4b7a9c2d5f8_work_orders.py`

- [x] **Step 1: Write failing metadata tests**

Add tests that import `WorkOrder` and `WorkOrderStatus`, assert enum values `assigned/in_progress`, package exports, table schema/name/columns, unique/check constraints, FK targets, and indexes.

- [x] **Step 2: Run metadata tests red**

Run: `pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q`
Expected: FAIL because `WorkOrder` is not exported.

- [x] **Step 3: Implement model and migration**

Create `work_order.py` with `WorkOrderStatus(str, enum.Enum)` and `WorkOrder(Base)`, using `SAEnum(... native_enum=False, values_callable=...)`, FK `users.id`, FK `utility_network.aois.id`, FK `utility_network.feeders.id`, unique `code`, status check, and indexes.

- [x] **Step 4: Run metadata tests green**

Run: `pytest utility_service/infrastructure/tests/test_network_model_metadata.py -q`
Expected: PASS.

## Task 2: Seed Spec And Create-Once Seed

**Files:**
- Create: `apps/backend/seeds/specs/seed_work_order_specs.py`
- Create: `apps/backend/seeds/tests/test_seed_work_order_specs.py`
- Create: `apps/backend/seeds/repositories/seed_work_order_repository.py`
- Create: `apps/backend/seeds/services/seed_work_order_service.py`
- Create: `apps/backend/seeds/tests/test_seed_work_order_service.py`
- Create: `apps/backend/seeds/runners/seed_work_orders.py`

- [x] **Step 1: Write failing seed spec tests**

Assert `SEED_WORK_ORDER_SPEC.code == "WO-001"`, stable id `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401`, assignee email `alexey.editor@example.local`, feeder code `synthetic_utility_feeder_01`, and `assigned` status.

- [x] **Step 2: Run seed spec tests red**

Run: `pytest seeds/tests/test_seed_work_order_specs.py -q`
Expected: FAIL because module does not exist.

- [x] **Step 3: Implement seed spec**

Create a frozen dataclass `SeedWorkOrderSpec` with `id`, `code`, `title`, `description`, `status`, `assignee_email`, `feeder_code`; export `SEED_WORK_ORDER_SPEC`.

- [x] **Step 4: Run seed spec tests green**

Run: `pytest seeds/tests/test_seed_work_order_specs.py -q`
Expected: PASS.

- [x] **Step 5: Write failing seed service tests**

Use a fake async session and `AsyncMock` repository. Cover create when absent, no-op when existing, and explicit missing dependency error for absent assignee/feeder/AOI.

- [x] **Step 6: Run seed service tests red**

Run: `pytest seeds/tests/test_seed_work_order_service.py -q`
Expected: FAIL because service/repository modules do not exist.

- [x] **Step 7: Implement seed repository/service/runner**

Repository split: `SeedWorkOrderRepository` owns `get_work_order_by_code` and `create_work_order`, `SeedUserRepository` owns assignee lookup, and `SeedUtilityDatasetRepository` owns `get_feeder_by_code` plus `get_first_aoi`. Service method: `ensure_work_order`, create-once transaction, no overwrite on existing `WO-001`, raise `SeedWorkOrderDependencyError` on missing dependency.

- [x] **Step 8: Run seed tests green**

Run: `pytest seeds/tests/test_seed_work_order_specs.py seeds/tests/test_seed_work_order_service.py -q`
Expected: PASS.

## Task 3: WorkOrder Use-Case Service

**Files:**
- Create: `apps/backend/utility_service/use_cases/domain/exceptions/work_order_api_error.py`
- Create: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
- Create: `apps/backend/utility_service/use_cases/services/work_order_service.py`
- Create: `apps/backend/utility_service/use_cases/tests/test_work_order_service.py`
- Modify: `apps/backend/utility_service/use_cases/deps.py`

- [x] **Step 1: Write failing service tests**

Use simple `SimpleNamespace` users/work orders, `AsyncMock` work order repository
and `AsyncMock` user repository. Cover loading actor by `actor_id`, assigned
active editor access, missing actor as `WORK_ORDER_ACTOR_NOT_FOUND`, reviewer
denied with `ROLE_NOT_ALLOWED`, inactive editor denied with `ROLE_NOT_ALLOWED`,
wrong editor denied with `WORK_ORDER_NOT_ASSIGNED`, missing order gives
`WORK_ORDER_NOT_FOUND`, `assigned -> in_progress`, and repeated start gives
`WORK_ORDER_STATE_CONFLICT`.

- [x] **Step 2: Run service tests red**

Run: `pytest utility_service/use_cases/tests/test_work_order_service.py -q`
Expected: FAIL because `WorkOrderService` does not exist.

- [x] **Step 3: Implement error, repository, service, deps factory**

`WorkOrderApiError` mirrors `UtilityNetworkApiError`. `WorkOrderRepository` exposes `get_by_id`, `get_by_code`, `list_assigned_to_user`, `save`. `WorkOrderService` receives `actor_id`, loads the current user via `UserRepository`, owns role/active/assignment/status rules and never depends on web API routers.

- [x] **Step 4: Run service tests green**

Run: `pytest utility_service/use_cases/tests/test_work_order_service.py -q`
Expected: PASS.

## Task 4: Documentation And Verification

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`
- Modify if needed: `docs/agent-memory/file-map.md`

- [x] **Step 1: Add implementation plan link to sprint README**

Add `План реализации backend foundation Work Orders Дня 5` after the Day 5 design link.

- [x] **Step 2: Run targeted unit suite**

Run from `apps/backend`: `pytest utility_service/infrastructure/tests/test_network_model_metadata.py seeds/tests/test_seed_work_order_specs.py seeds/tests/test_seed_work_order_service.py utility_service/use_cases/tests/test_work_order_service.py -q`
Expected: PASS.

- [x] **Step 3: Run memory check because docs/agent-memory changed earlier**

Run from repo root: `python scripts/check-memory-needed.py --check` or bundled Python equivalent.
Expected: `Memory update check passed.`

- [x] **Step 4: Search for stale paths and placeholder markers**

Run the stale-path and placeholder-marker search against release docs, memory map,
`Code_wiki/index.md`, and `Vision_wiki/decisions/followups/index.md`, excluding
this implementation plan so the documented verification text does not self-match.
Expected: no matches.

## Self-Review

- Spec coverage: model, statuses, assignment, seed, service checks, unit tests, no public API/frontend/EditVersion are covered by Tasks 1-4.
- Placeholder scan: no unresolved placeholder markers or vague edge-case instructions.
- Type consistency: `WorkOrderStatus`, `WorkOrder`, `SeedWorkOrderSpec`, `SeedWorkOrderService`, `WorkOrderRepository`, `WorkOrderService`, and `WorkOrderApiError` names are consistent across tasks.
