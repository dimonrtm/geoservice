---
title: CI And Quality Gates
type: runbook
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [ci, tests, lint, build]
---

# CI And Quality Gates

CI описан в `.github/workflows/ci.yml` и разделен на backend/frontend jobs.

## Backend

Backend jobs собирают Docker image `geoservice-backend:dev` из `apps/backend/app` и запускают:

- `black --check .`
- `ruff check .`
- `pytest`

После format/lint/test собирается prod image `geoservice-backend:prod`.

Отдельный smoke-test поднимает `postgis` и `backend` через `infra/docker-compose.yml`, ждет healthy backend и проверяет `/health` внутри container.

Локальные настройки:

- `apps/backend/pyproject.toml` задает `ruff`/`black` line length `100`, target Python `3.12`, pytest `testpaths = ["tests"]`.
- Backend test files лежат в `apps/backend/app/tests`.

## Frontend

Frontend jobs используют Node 20 и `npm ci` в `apps/frontend`, затем запускают:

- `npm run format:check`
- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run build`

Frontend unit tests лежат рядом с кодом как `*.test.ts`.

## Wiki Checks

Knowledge wiki проверяется локально:

```powershell
python scripts/lint-wiki.py --root .
```

Для durable изменений process/plan/wiki rules есть дополнительная проверка:

```powershell
python scripts/check-memory-needed.py --check
```

## Связанные Ноды

- [[../правила_и_стиль/testing_strategy]]
- [[../deployment/docker_compose]]
