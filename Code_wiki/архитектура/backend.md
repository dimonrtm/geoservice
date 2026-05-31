---
title: Backend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [backend, fastapi, postgis, architecture]
---

# Backend Architecture

Backend GeoService находится в `apps/backend/app` и построен как FastAPI-приложение поверх async SQLAlchemy, Alembic и PostGIS.

## Входные Точки

- `apps/backend/app/main.py` создает `FastAPI`, подключает CORS, routers и exception handlers.
- `apps/backend/app/api/lifespan.py` кладет `WebSocketConnectionManager` в `app.state` и закрывает SQLAlchemy engine при shutdown.
- `/health` возвращает простой health-check для Docker Compose и CI smoke-test.

## Слои Кода

- `api/` содержит HTTP/WebSocket routers, dependency wiring и exception handlers.
- `services/` содержит бизнес-операции: auth, layer read, feature CRUD, realtime publishing, demo seed.
- `repositories/` изолирует SQLAlchemy-запросы к users, layers и geometry tables.
- `models/` описывает таблицы `users`, `layers` и feature-таблицы по типам геометрии.
- `schemas/` содержит Pydantic DTO для входов, ответов и GeoJSON.
- `domain/` содержит bbox parsing, feature registry и domain exceptions.

## Конфигурация И Безопасность

`apps/backend/app/core/settings.py` читает `.env` через `pydantic-settings`. При `DEV_MODE=false` `JWT_SECRET` обязан быть явно задан и не может оставаться `CHANGE_ME_IN_ENV`.

HTTP auth использует JWT Bearer:

- `/api/v1/auth/login` выдает token и user payload.
- `/api/v1/auth/me` валидирует token и перечитывает пользователя из БД.
- `/api/v1/auth/dev-login` регистрируется только при включенном `DEV_MODE`.

Роли:

- `viewer` и `editor` могут читать layers/features и подписываться на realtime.
- Только `editor` может создавать, изменять и удалять features.

## Связанные Ноды

- [[api_and_realtime]]
- [[data_model]]
- [[../dev_setup/local_development]]
- [[../deployment/docker_compose]]
