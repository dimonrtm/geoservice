---
title: Backend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-06-20
source: repository-change:2026-06-20
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

## WorkOrder Foundation

`WorkOrder` теперь является агрегатом в границе `work_order`. `WorkOrderService`
находится в `utility_service.use_cases`, принимает `actor_id`, загружает
актуального `User` через `UserRepository` и централизует правила:

- пользователь `actor_id` должен существовать и быть активным `Editor`;
- work order должен существовать;
- `assignee_id` должен совпадать с текущим пользователем;
- переход `assigned -> in_progress` выполняется через service внутри
  `AsyncSession` transaction boundary и сохраняется repository;
- повторный старт или другой несовместимый статус возвращает
  `WORK_ORDER_STATE_CONFLICT`.

`WorkOrderRepository` является единым writer/repository агрегата `WorkOrder`: он
читает сам work order, сохраняет status transitions, ищет открытую
`EditVersion` и пишет `work_order.edit_versions`,
`edit_version_features`/`edit_version_associations` из уже переданных baseline
rows. Чтение пользователя остается ответственностью `UserRepository`, чтение
`DefaultState` и его features/associations - `DefaultStateRepository`.
`DefaultStateRepository.get_active_aggregate_by_work_order_id` выполняет один
SQL round trip с независимыми JSONB aggregation subqueries для features и
associations, чтобы не делать несколько repository calls и не получать
`features x associations` row explosion. Текст запроса вынесен в
`utility_service/infrastructure/postgresql/sql/default_state_aggregate.sql` и
читается один раз при импорте repository module в module-level SQLAlchemy
statement. Отдельного `EditVersionRepository` в финальной границе нет.

## EditVersion Foundation

`EditVersionService` открывает изолированную edit version от активного
`DefaultState` назначенного work order. Service остается application-layer
оркестратором: он принимает `actor_id`, работает внутри `AsyncSession`
transaction boundary и связывает данные из разных схем только через repositories
(`UserRepository`, `WorkOrderRepository`, `DefaultStateRepository`), а не через
cross-schema FK или прямые обращения к чужим моделям.

Правила открытия:

- actor должен быть активным `Editor`;
- work order видим только своему assignee; чужой или отсутствующий work order
  маскируется как `404 WORK_ORDER_NOT_FOUND`;
- `assigned` без открытой edit version требует активный `DefaultState` этого
  work order; `EditVersionService` через один aggregate-вызов
  `DefaultStateRepository` получает baseline features/associations, затем
  передает их в `WorkOrderRepository`, который создает deep copy в
  `work_order.edit_versions`, `edit_version_features` и
  `edit_version_associations` с сохранением UUID features/associations и записывает
  `base_network_revision = DefaultState.base_network_revision` и переводит work
  order в `in_progress` в той же transaction boundary;
- `in_progress` с уже открытой edit version возвращает существующую версию,
  обновляя `last_opened_at`;
- рассинхрон work order и edit version возвращает
  `422 WORK_ORDER_CONTEXT_INVALID`, а несовместимый статус work order -
  `409 WORK_ORDER_STATE_CONFLICT`.

`POST /api/v1/work-orders/{work_order_id}/edit-versions` является первым
публичным Work Orders endpoint: он требует `Editor`, возвращает `201` при
создании и `200` при повторном открытии существующей версии.

## Конфигурация И Безопасность

`apps/backend/utility_service/utils/settings.py` читает `.env` через `pydantic-settings`. При
`DEV_MODE=false` `JWT_SECRET` обязан быть явно задан и не может оставаться
`CHANGE_ME_IN_ENV`.

HTTP auth использует JWT Bearer:

- `/api/v1/auth/login` выдает token и user payload.
- `/api/v1/auth/me` валидирует token и перечитывает пользователя из БД.
- `/api/v1/auth/dev-login` удален; пользовательский вход поддерживается через
  `/api/v1/auth/login` и `/api/v1/auth/me`.

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
