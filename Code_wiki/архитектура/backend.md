---
title: Backend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-06-16
source: repository-change:2026-06-16
tags: [backend, fastapi, postgis, architecture]
---

# Backend Architecture

Backend GeoService находится в `apps/backend` и собран вокруг пакета `utility_service`.
Код разделен на пакеты с направлением зависимостей от внешнего адаптера к use cases и
инфраструктуре.

## Входные Точки

- `apps/backend/utility_service/web_api/main.py` создает `FastAPI`, подключает CORS,
  routers и exception handlers.
- `apps/backend/utility_service/web_api/api/lifespan.py` кладет
  `WebSocketConnectionManager` в `app.state` и закрывает runtime resources через
  `utility_service.use_cases.deps`.
- `/health` возвращает простой health-check для Docker Compose и CI smoke-test.
- Alembic запускается из `apps/backend/alembic.ini`; миграции находятся в
  `apps/backend/utility_service/infrastructure/postgresql/alembic`.

## Пакеты И Границы

- `utility_service.web_api` содержит FastAPI controllers, routers, WebSocket endpoints,
  lifespan и exception handlers. Этот пакет не импортирует `utility_service.infrastructure`.
- `utility_service.use_cases` содержит dependency factories в `deps.py`, Pydantic DTO,
  domain exceptions и application services. Этот пакет не импортирует `utility_service.web_api`.
- `utility_service.infrastructure.postgresql` содержит SQLAlchemy models, repositories,
  session factory и Alembic migrations.
- `utility_service.domain_services` содержит доменные helper-функции без web controllers.
- `utility_service.utils` содержит общие настройки и password helpers.
- `seeds` остается отдельным backend-пакетом для startup/demo data logic.

`web_api` импортирует dependency factories напрямую из `utility_service.use_cases.deps`.
Pydantic schemas живут в `utility_service.use_cases.schemas`. Разрешенное направление
runtime-зависимостей: `web_api -> use_cases -> infrastructure`; обратная зависимость на
`web_api` запрещена и проверяется архитектурным тестом.

## Utility Read Path

`GET /api/v1/utility-network/feeders/{feederId}` доступен только активному `Editor`.
`UtilityNetworkRepository.get_feeder_aggregate()` выполняет один SQL round trip и возвращает
feeder вместе с тремя независимо отсортированными JSONB aggregates: features, associations и
пересекающиеся AOI. AOI выбираются через correlated `EXISTS` + `ST_Intersects`; плоский JOIN
коллекций не используется, чтобы не создавать размножение строк.

## Конфигурация И Безопасность

`apps/backend/utility_service/utils/settings.py` читает `.env` через `pydantic-settings`. При
`DEV_MODE=false` `JWT_SECRET` обязан быть явно задан и не может оставаться
`CHANGE_ME_IN_ENV`.

HTTP auth использует JWT Bearer:

- `/api/v1/auth/login` выдает token и user payload.
- `/api/v1/auth/me` валидирует token и перечитывает пользователя из БД.
- `/api/v1/auth/dev-login` регистрируется только при включенном `DEV_MODE`.

Роли:

- `editor` и `reviewer` могут читать layers/features и подписываться на realtime.
- Только `editor` может создавать, изменять и удалять features.
- `get_current_user` после JWT decode загружает актуального `User` из БД и проверяет
  `is_active`; роль из JWT не является source of truth.
- `require_editor` и `require_reviewer` реализуют взаимоисключающие role guards без прямой
  зависимости `web_api` от SQLAlchemy model enum.

## Связанные Ноды

- [[api_and_realtime]]
- [[data_model]]
- [[../dev_setup/local_development]]
- [[../deployment/docker_compose]]
- [[../правила_и_стиль/testing_strategy]]
