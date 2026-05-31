---
title: Docker Compose Deployment
type: runbook
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [deployment, docker-compose, postgis]
---

# Docker Compose Deployment

Репозиторий содержит Dockerfile для backend/frontend и Compose-конфигурацию в `infra/`.

## Backend Image

`apps/backend/app/Dockerfile` использует multi-stage:

- `base` на `python:3.12-slim`, устанавливает `gcc` и `libpq-dev`;
- `deps` устанавливает `requirements.txt`;
- `dev` добавляет `ruff`, `black`, `pytest` и копирует приложение;
- `prod` копирует приложение без дополнительных dev-команд.

## Frontend Image

`apps/frontend/Dockerfile` использует:

- Node 20 Alpine для install/build;
- `dev` target для `npm run dev -- --host 0.0.0.0 --port 5173`;
- `build` target для `npm run build`;
- nginx 1.27 Alpine для production static hosting.

## Compose Services

`infra/docker-compose.yml` описывает `postgis`, `migrate`, `backend`, `frontend-dev`, `frontend-prod` и volume `geo_pgdata`.

Важные детали:

- `postgis` имеет healthcheck через `pg_isready`.
- `backend` зависит от healthy `postgis`, запускает migrations, demo seed и uvicorn.
- `backend` healthcheck дергает `http://localhost:8000/health`.
- `frontend-dev` зависит от healthy backend.
- `frontend-prod` собирает статический frontend и отдает через nginx.

`infra/docker-compose.override.yml` раскрывает порты `5432` и `8000` и ожидает переменные без default-значений. `infra/docker-compose.full.yml` на snapshot дату пустой.

## Связанные Ноды

- [[../dev_setup/local_development]]
- [[../сборка/ci_and_quality]]
