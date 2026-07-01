---
title: Local Development
type: runbook
status: active
created: 2026-05-30
updated: 2026-06-22
source: repository-change:2026-06-22
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
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```

Сервисы:

- `postgis` - PostgreSQL/PostGIS 16-3.4 с init script `infra/docker/postgis/init/01-postgis.sql`.
- `backend` - FastAPI dev image на `apps/backend/app/Dockerfile`, порт `8000`.
- `frontend-dev` - Vite dev server, порт `5173`, профиль `dev`.
- `frontend-prod` - nginx build, порт `8080`, профиль `prod`.
- `migrate` - отдельный profile service для `alembic upgrade head`.

Production-safe base compose `infra/docker-compose.yml` запускает
`utility_service` через `bash scripts/start_api.sh` без demo seed chain.
Явный demo/dev compose layer `infra/docker-compose.demo.yml` при запуске с
`--env-file demo.env` стартует backend через `bash scripts/start_utility_service.sh`;
этот script выполняет migrations, demo-user seed, utility dataset seed и
WorkOrder seed при старте.

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

`python -m seeds.runners.seed_work_orders` создаёт create-once `WO-001` после
demo users и utility dataset. Повторный запуск при существующем `WO-001` не
перезаписывает assignee, status, title или description, но гарантирует активный
per-WorkOrder `DefaultState`, скопированный из текущего
`synthetic_utility_feeder_01`.

Legacy credentials `editor@example.com` и `viewer@example.com` удалены.
После login `Editor` попадает на экран `Мои наряды`: список назначенных ему work
orders и пустую карту с basemap. Выбор work order только подсвечивает строку в
списке; `EditVersion` не открывается до отдельного явного workflow. `Reviewer`
видит отдельный placeholder без editor workspace; reviewer queue ещё не реализована.

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

`infra/demo.env` содержит public demo-only значения для локального запуска.
Production-safe `infra/docker-compose.yml` требует `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DATABASE_URL` и `JWT_SECRET` через private `.env`, shell
environment или CI secrets.

Если после перехода на `infra/demo.env` `utility_service` становится unhealthy,
а `docker compose logs utility_service` показывает
`password authentication failed for user "postgres"`, причина обычно в старом
Docker volume `infra_geo_pgdata`, который уже был инициализирован с другим
паролем. Для disposable demo DB выполните
`docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v`
и затем повторите demo/dev запуск. Команда удаляет локальные данные Postgres.

## Связанные Ноды

- [[../архитектура/backend]]
- [[../архитектура/frontend]]
- [[../deployment/docker_compose]]
