---
title: Docker Compose Deployment
type: runbook
status: active
created: 2026-05-30
updated: 2026-06-13
source: repository-change:2026-06-13
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

## Проверенный Контракт

Изменение ролей Дня 2 проверено без изменения Dockerfile и Compose-файлов:

- base Compose `postgis + backend` поднимается healthy и выполняет migration и seed;
- upgrade существующего volume переводит Alembic на `b82a5f2d91c3`, удаляет
  legacy `viewer` и сохраняет существующих `editor`;
- clean install на отдельном временном volume создаёт ровно три целевых demo users;
- профили `dev` и `prod` отвечают соответственно на `5173` и `8080`, backend
  отвечает на `8000`;
- повторный restart backend и ручной `python seed_demo_users.py` не создают
  дубликаты.

Для локального clean-install smoke PostGIS нужно считать готовым после
устойчивых SQL-проверок: `pg_isready` может кратко отвечать во время временного
init-сервера до финального restart entrypoint.

## Связанные Ноды

- [[../dev_setup/local_development]]
- [[../сборка/ci_and_quality]]
