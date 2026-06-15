---
title: Local Development
type: runbook
status: active
created: 2026-05-30
updated: 2026-06-15
source: repository-change:2026-06-15
tags: [dev-setup, docker, backend, frontend]
---

# Local Development

Основной локальный сценарий GeoService завязан на Docker Compose из `infra/`.

## Требования

- Python 3.12+
- Node 20+
- Docker Desktop / WSL2

## Docker Compose Dev

Запуск dev-профиля:

```powershell
cd infra
docker compose --profile dev up --build
```

Сервисы:

- `postgis` - PostgreSQL/PostGIS 16-3.4 с init script `infra/docker/postgis/init/01-postgis.sql`.
- `backend` - FastAPI dev image на `apps/backend/app/Dockerfile`, порт `8000`.
- `frontend-dev` - Vite dev server, порт `5173`, профиль `dev`.
- `frontend-prod` - nginx build, порт `8080`, профиль `prod`.
- `migrate` - отдельный profile service для `alembic upgrade head`.

Backend в основном compose сам выполняет migrations, demo-user seed и utility
dataset seed при старте.

## Demo Users

`python -m seeds.runners.seed_demo_users` поддерживает baseline
demo-пользователей:

- `alexey.editor@example.local` / `alexey-editor-password`, роль `editor`.
- `bolat.editor@example.local` / `bolat-editor-password`, роль `editor`.
- `marina.reviewer@example.local` / `marina-reviewer-password`, роль `reviewer`.

Seed использует цепочку `SeedDemoUserService -> SeedUserRepository`, стабильные
UUID и при каждом старте backend приводит demo users к ожидаемым роли, паролю
и `is_active=true`. Повторный запуск не создаёт дубликаты.

`python -m seeds.runners.seed_utility_dataset` создаёт
`synthetic_utility_feeder_01`: 1 AOI, 19 features и 9 associations. Повторный
запуск при существующем feeder является no-op и сохраняет ручные изменения.

Legacy credentials `editor@example.com` и `viewer@example.com` удалены.
`Editor` видит существующий map/editor workspace. `Reviewer` видит отдельный
placeholder без editor workspace; reviewer queue ещё не реализована.

## Переменные

Backend:

- `DATABASE_URL`
- `DEV_MODE`
- `JWT_SECRET`
- `JWT_ALG`
- `ACCESS_TOKEN_TTL_MIN`
- `CORS_ORIGINS`

Frontend:

- `VITE_API_BASE_URL`

В `infra/.env.example` есть пример DB-настроек, но он не покрывает все переменные backend/frontend.

## Связанные Ноды

- [[../архитектура/backend]]
- [[../архитектура/frontend]]
- [[../deployment/docker_compose]]
