---
title: Testing Strategy
type: note
status: active
created: 2026-05-30
updated: 2026-07-02
source: repository-change:2026-07-02
tags: [testing, backend, frontend, quality]
---

# Testing Strategy

В репозитории есть backend pytest suite, frontend Vitest suite и отдельные тесты
knowledge-pipeline scripts.

## Backend Tests

Backend unit tests лежат рядом с соответствующими пакетами:

- `apps/backend/utility_service/web_api/tests`
- `apps/backend/utility_service/use_cases/tests`
- `apps/backend/utility_service/domain_services/tests`
- `apps/backend/utility_service/infrastructure/tests`
- `apps/backend/utility_service/utils/tests`
- `apps/backend/seeds/tests`

Backend integration tests лежат в `apps/backend/tests/integration_tests`.
Общие root-level проверки, которые не являются unit или integration тестом конкретного пакета,
могут оставаться в `apps/backend/tests`; сейчас там находится архитектурная проверка импортных
границ и sanity test.

Live service smoke runners лежат в `apps/backend/tests/smoke`. Файлы runner не
начинаются с `test_`, чтобы обычный `pytest` не требовал поднятый сервис. Их
поведение покрывается unit tests в той же папке, а live-запуск выполняется
отдельным CI/Compose step.

Покрытые области:

- auth service, `utility_service/utils/passwords.py` и demo user seed;
- settings security validation;
- bbox validation;
- exception handlers;
- feature service CRUD/version behavior;
- feature realtime publisher;
- realtime WebSocket ticket auth: ticket issue, single-use consume, expired/reused/wrong-layer rejection и layer websocket endpoint;
- realtime connection manager;
- utility dataset specs, create-once/no-op service и rollback behavior;
- work order model metadata, schema boundary checks for `user`,
  `utility_network` и `work_order`, stable `WO-001` seed spec, create-once work
  order seed service, creation of per-WorkOrder `DefaultState` и
  assignment/status use-case rules;
- edit version metadata, aggregate `WorkOrderRepository`, `DefaultState`
  repository lookup, `EditVersionService` rules, Work Orders API open/reopen
  behavior, `baseNetworkRevision` response contract и structured errors;
- Work Orders `assigned-to-me` API contract, Editor-only access, compact response
  without audit/date fields, service delegation и repository sorting by
  `updated_at DESC`, `code ASC`;
- full path workspace smoke runner: login seeded `Editor`, получить `WO-001`
  через `assigned-to-me`, открыть или переоткрыть `EditVersion`, загрузить
  workspace и проверить AOI, 19 features и 9 associations;
- PostGIS persistence, spatial AOI intersection и single-query feeder aggregate;
- migration integration test для `a8c1f2d3e4b5_edit_versions.py`, включая
  upgrade/downgrade/upgrade cycle, `utility_network.network_states`,
  per-WorkOrder `DefaultState`, `work_order.edit_versions`, constraints и
  partial unique index `uq_edit_versions_open_work_order`;
- utility mapping, structured errors и Editor-only API access;
- architecture boundaries между `web_api`, `use_cases` и `infrastructure`.

## Frontend Tests

Frontend tests находятся рядом с TypeScript modules:

- `stores/auth.test.ts`
- `stores/edit.test.ts`
- `stores/workOrders.test.ts`
- `contracts/geojson.test.ts`
- `contracts/realtime.test.ts`
- `map/feature-grid.test.ts`
- `App.test.ts`
- `components/EditorWorkOrdersView.test.ts`
- `components/MapView.test.ts`
- `composables/map/useFeatureTileCache.test.ts`
- `composables/map/useLayerRealtime.test.ts`

Тесты покрывают contract guards, auth/edit/workOrders stores, feature grid/tile
cache, realtime reconnect/event parsing, role-specific app shell, пустой режим
карты для экрана `Мои наряды` и локальную подсветку выбранного work order. Vitest
использует `jsdom`, чтобы Vue component tests могли монтировать DOM.

## Pipeline Tests

Scripts tests лежат в `scripts/tests`:

- `test_lint_wiki.py`
- `test_check_memory_needed.py`
- `test_memory_audit.py`

Они защищают wiki frontmatter/wikilinks, узкий gate обязательной agent memory для изменений
operating rules и read-only аудит жизненного цикла памяти.

## Команды

Backend:

```powershell
cd apps/backend
pytest
black --check .
ruff check .
```

Focused smoke-runner check:

```powershell
cd apps/backend
pytest tests/smoke/test_full_path_workspace_smoke.py -q
```

Live Compose smoke после healthy `utility_service`:

```powershell
cd infra
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
```

Docker/CI-equivalent backend:

```powershell
docker build --target dev -t utility_service:dev apps/backend
docker run --rm --entrypoint bash utility_service:dev -lc "black --check ."
docker run --rm --entrypoint bash utility_service:dev -lc "ruff check ."
docker run --rm --entrypoint bash utility_service:dev -lc "pytest"
```

Frontend:

```powershell
cd apps/frontend
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Wiki:

```powershell
python scripts/lint-wiki.py --root .
python scripts/check-memory-needed.py --check
python scripts/audit-memory.py --root .
```

Findings `audit-memory.py` являются отчетом для ревизии, а не автоматическим разрешением на
удаление. Изменять или удалять найденные записи можно только после явного подтверждения
пользователя.

## Связанные Ноды

- [[../сборка/ci_and_quality]]
- [[../архитектура/backend]]
- [[../архитектура/frontend]]
