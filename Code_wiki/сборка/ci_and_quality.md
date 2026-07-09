---
title: CI And Quality Gates
type: runbook
status: active
created: 2026-05-30
updated: 2026-07-09
source: repository-change:2026-07-09
tags: [ci, tests, lint, build]
---

# CI And Quality Gates

CI описан в `.github/workflows/ci.yml` и разделен на backend/frontend jobs.

## Backend

Backend jobs собирают Docker image `utility_service:dev` из `apps/backend` и запускают:

- `black --check .`
- `ruff check .`
- `pytest`

После format/lint/test собирается prod image `utility_service:prod`.

Отдельный smoke-test поднимает `postgis` и `utility_service` через
`infra/docker-compose.yml`, ждет healthy `utility_service` и проверяет `/health` внутри
container.

Smoke job также запускает PostGIS tests network model, migration cycle, utility dataset seed и
single-query repository. После EditVersion foundation в этот же блок добавлен
`pytest tests/integration_tests/test_edit_version_migration.py -q`, который
проверяет миграцию `a8c1f2d3e4b5_edit_versions.py`, `utility_network`
baseline tables, `work_order` edit tables, partial unique index на одну
открытую edit version, GiST index `ix_edit_version_features_geometry` и lookup
index `ix_edit_version_associations_edit_version_to_feature_id`. Этот migration
contract дополнительно группирует реальные индексы в каталоге БД по таблице,
access method и колонкам, чтобы не допустить дублей целевых index groups.
Integration tests лежат в
`apps/backend/tests/integration_tests`, а CI запускает их как
`pytest tests/integration_tests/<test_file>.py -q` внутри `utility_service`.
Migration-cycle tests проверяют clean production-like Alembic chain:
`upgrade -> downgrade -> upgrade` для user role, utility network и edit-version
слоёв. Они больше не проверяют repair старых stamped volumes и не ожидают
legacy `utility_network.aois`. Demo seed chain проверяется отдельными
seed-проверками и authenticated API smoke gates.
Для локального smoke после уже поднятого dev volume также нужен
`python -m seeds.runners.seed_work_orders`, если проверяется создание
`DefaultState`/`EditVersion` для demo work order. Затем Editor login проверяет
полный feeder response с 19 features и 9 associations.

После Day 13 в `smoke_test` добавлен full path workspace API smoke:
`python tests/smoke/full_path_workspace_smoke.py` внутри контейнера
`utility_service`. Runner проверяет живой HTTP-путь
`POST /api/v1/auth/login -> GET /api/v1/work-orders/assigned-to-me ->
POST /api/v1/work-orders/{workOrderId}/edit-versions ->
GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`.
В отличие от прежнего hardcoded workspace smoke, этот gate берет `workOrderId`
из assigned list и проверяет связку login/assignment/open/workspace на seeded
`WO-001`, expected AOI, 19 features и 9 associations. Browser E2E tooling в
этот gate не входит.

Для raw SQL workspace aggregate локальный focused gate дополнительно включает
repository contract tests для `sql/workspace_aggregate.sql`, full seed-chain
integration file и regression, где association с endpoint feature вне AOI
исключается из workspace response. Format/lint scope остается стандартным:
`black --check` и `ruff check` по измененным backend Python files.

Локальные настройки:

- `apps/backend/pyproject.toml` задает `ruff`/`black` line length `100`, target Python `3.12`
  и pytest discovery для package-local unit tests, `seeds/tests` и `tests`.
- Unit tests backend лежат рядом с соответствующими пакетами:
  `utility_service/web_api/tests`, `utility_service/use_cases/tests`,
  `utility_service/domain_services/tests`, `utility_service/infrastructure/tests`,
  `utility_service/utils/tests`, `seeds/tests`.
- `apps/backend/conftest.py` задает безопасные test-only defaults для `DATABASE_URL`,
  `DEV_MODE` и `JWT_SECRET`, поэтому чистый CI container может импортировать DB-backed auth
  modules без внешнего runtime env.
- Архитектурный тест в `apps/backend/tests/test_architecture_boundaries.py` запрещает
  `web_api -> infrastructure`, `use_cases -> web_api` и `infrastructure -> web_api`.

## Frontend

Frontend jobs используют Node 20 и `npm ci` в `apps/frontend`, затем запускают:

- `npm run format:check`
- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run build`

Frontend unit tests лежат рядом с TypeScript modules как `*.test.ts`.
Vitest использует `jsdom`, поэтому CI покрывает не только store/contract modules,
но и Vue component shell tests для `App.vue`, `EditorWorkOrdersView.vue` и
`MapView.vue`.

## Wiki Checks

Knowledge wiki проверяется локально:

```powershell
python scripts/lint-wiki.py --root .
```

Для durable изменений process/plan/wiki rules есть дополнительная проверка:

```powershell
python scripts/check-memory-needed.py --check
```

Жизненный цикл agent memory проверяется read-only аудитом:

```powershell
python scripts/audit-memory.py --root .
```

Findings `audit-memory.py` являются отчетом для ревизии, а не автоматическим разрешением на
удаление. Изменять или удалять найденные записи можно только после явного подтверждения
пользователя.

## Связанные Ноды

- [[../правила_и_стиль/testing_strategy]]
- [[../deployment/docker_compose]]
