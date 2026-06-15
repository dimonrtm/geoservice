---
title: Backend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-06-15
source: repository-change:2026-06-15
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
- `services/` содержит runtime business operations: auth, layer read, feature
  CRUD, realtime publishing и чтение utility network.
- `repositories/` изолирует runtime SQLAlchemy-запросы к users, layers,
  geometry tables и utility network.
- `models/` описывает таблицы `users`, `layers` и feature-таблицы по типам геометрии.
- `schemas/` содержит Pydantic DTO для входов, ответов и GeoJSON.
- `domain/` содержит bbox parsing, feature registry и domain exceptions.
- `seeds/` изолирует startup data logic в подпакетах `repositories`,
  `services`, `specs` и `runners`; seed-код не использует runtime repositories
  или services.

Общая password logic находится в нейтральном `core/passwords.py` и
используется как auth runtime, так и demo-user seed.

## Utility Read Path

`GET /api/v1/utility-network/feeders/{feederId}` доступен только активному
`Editor`. `UtilityNetworkRepository.get_feeder_aggregate()` выполняет один SQL
round trip и возвращает feeder вместе с тремя независимо отсортированными
JSONB aggregates: features, associations и пересекающиеся AOI. AOI выбираются
через correlated `EXISTS` + `ST_Intersects`; плоский JOIN коллекций не
используется, чтобы не создавать размножение строк.

## Конфигурация И Безопасность

`apps/backend/app/core/settings.py` читает `.env` через `pydantic-settings`. При `DEV_MODE=false` `JWT_SECRET` обязан быть явно задан и не может оставаться `CHANGE_ME_IN_ENV`.

HTTP auth использует JWT Bearer:

- `/api/v1/auth/login` выдает token и user payload.
- `/api/v1/auth/me` валидирует token и перечитывает пользователя из БД.
- `/api/v1/auth/dev-login` регистрируется только при включенном `DEV_MODE`.

Роли:

- `editor` и `reviewer` могут читать layers/features и подписываться на realtime.
- Только `editor` может создавать, изменять и удалять features.
- `get_current_user` после JWT decode загружает актуального `User` из БД и
  проверяет `is_active`; роль из JWT не является source of truth.
- `require_editor` и `require_reviewer` реализуют взаимоисключающие role guards.

## Связанные Ноды

- [[api_and_realtime]]
- [[data_model]]
- [[../dev_setup/local_development]]
- [[../deployment/docker_compose]]
