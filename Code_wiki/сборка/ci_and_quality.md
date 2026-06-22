---
title: CI And Quality Gates
type: runbook
status: active
created: 2026-05-30
updated: 2026-06-22
source: repository-change:2026-06-22
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
baseline tables, `work_order` edit tables и partial unique index на одну
открытую edit version. Integration tests лежат в
`apps/backend/tests/integration_tests`, а CI запускает их как
`pytest tests/integration_tests/<test_file>.py -q` внутри `utility_service`.
Migration cycle удаляет данные utility schema при downgrade, поэтому перед authenticated API
smoke CI повторно запускает `python -m seeds.runners.seed_utility_dataset`.
Для локального smoke после уже поднятого dev volume также нужен
`python -m seeds.runners.seed_work_orders`, если проверяется создание
`DefaultState`/`EditVersion` для demo work order. Затем Editor login проверяет
полный feeder response с 19 features и 9 associations.

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
