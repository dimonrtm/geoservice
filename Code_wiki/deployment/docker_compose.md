---
title: Docker Compose Deployment
type: runbook
status: active
created: 2026-05-30
updated: 2026-06-17
source: repository-change:2026-06-17
tags: [deployment, docker-compose, postgis]
---

# Docker Compose Deployment

Репозиторий содержит Dockerfile для backend/frontend и Compose-конфигурацию в `infra/`.
Backend runtime-сервис называется `utility_service`; контейнер также имеет
`container_name: utility_service`.

## Backend Image

`apps/backend/Dockerfile` использует multi-stage:

- `base` на `python:3.12-slim`, устанавливает `gcc` и `libpq-dev`;
- `deps` устанавливает `apps/backend/requirements.txt`;
- `dev` добавляет `ruff`, `black`, `pytest` и копирует приложение;
- `prod` копирует приложение без дополнительных dev-команд.

Build context для backend: `apps/backend`.

## Frontend Image

`apps/frontend/Dockerfile` использует:

- Node 20 Alpine для install/build;
- `dev` target для `npm run dev -- --host 0.0.0.0 --port 5173`;
- `build` target для `npm run build`;
- nginx 1.27 Alpine для production static hosting.

## Compose Services

`infra/docker-compose.yml` описывает `postgis`, `migrate`, `utility_service`,
`frontend-prod` и volume `geo_pgdata`.

Важные детали:

- `postgis` имеет healthcheck через `pg_isready`.
- `migrate` собирается из `../apps/backend/` и запускает `alembic upgrade head`.
- `infra/docker-compose.yml` является production-safe baseline: `utility_service`
  собирается из backend target `prod`, получает `DEV_MODE=false`, требует
  `JWT_SECRET` и DB env через `${VAR:?message}` и запускает
  `bash scripts/start_api.sh` без demo seed chain.
- `infra/docker-compose.demo.yml` является явным demo/dev layer. Он используется
  вместе с `--env-file demo.env`, переопределяет backend target на `dev`, открывает
  порты `5432`, `8000`, `5173`, подключает `frontend-dev` и запускает
  `bash scripts/start_utility_service.sh`.
- `utility_service` healthcheck дергает `http://localhost:8000/health`.
- `frontend-dev` и `frontend-prod` зависят от healthy `utility_service`.

`infra/docker-compose.full.yml` на snapshot дату пустой.

## Связанные Ноды

- [[../dev_setup/local_development]]
- [[../сборка/ci_and_quality]]
- [[../архитектура/backend]]
