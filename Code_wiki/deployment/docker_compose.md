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
`frontend-dev`, `frontend-prod` и volume `geo_pgdata`.

Важные детали:

- `postgis` имеет healthcheck через `pg_isready`.
- `migrate` собирается из `../apps/backend/` и запускает `alembic upgrade head`.
- `utility_service` зависит от healthy `postgis` и запускает
  `bash scripts/start_utility_service.sh`. Скрипт выполняет `alembic upgrade head`,
  затем `python -m seeds.runners.seed_demo_users`,
  `python -m seeds.runners.seed_utility_dataset`,
  `python -m seeds.runners.seed_work_orders` и после seed запускает
  `uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000`.
- `utility_service` healthcheck дергает `http://localhost:8000/health`.
- `frontend-dev` и `frontend-prod` зависят от healthy `utility_service`.

`infra/docker-compose.override.yml` раскрывает порты `5432` и `8000` и ожидает переменные без
default-значений. `infra/docker-compose.full.yml` на snapshot дату пустой.

## Связанные Ноды

- [[../dev_setup/local_development]]
- [[../сборка/ci_and_quality]]
- [[../архитектура/backend]]
