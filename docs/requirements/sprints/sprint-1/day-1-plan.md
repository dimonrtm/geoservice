# День 1: фиксация контрактов Sprint 1

## Цель дня

- Зафиксировать login contract для Sprint 1.
- Зафиксировать WebSocket contract для realtime по слою.
- Описать reconnect-поведение клиента после потери соединения.
- Явно отделить in-scope и out-of-scope Sprint 1.
- Определить Definition of Done для завершения первого дня и границы приёмки Sprint 1.

## Результат дня

- Есть согласованный контракт `POST /api/v1/auth/login`.
- Есть согласованный контракт `GET /api/v1/auth/me`.
- Есть согласованный WebSocket endpoint `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`.
- Есть зафиксированные payload'ы `feature_created`, `feature_updated`, `feature_deleted`.
- Есть правила reconnect и повторной синхронизации активного слоя.
- Есть зафиксированный список того, что не входит в Sprint 1.

## Задачи

1. Сверить текущий [requirements-compliance-audit.md](/C:/Repositories/geoservice/docs/requirements/requirements-compliance-audit.md) с [geoservice-requirements.md](/C:/Repositories/geoservice/docs/requirements/geoservice-requirements.md) и [geoservice-prd-v1.md](/C:/Repositories/geoservice/docs/requirements/geoservice-prd-v1.md).
2. Выделить только Sprint-1 изменения публичных контрактов без захвата задач Sprint 2 и следующих этапов.
3. Описать request/response для `POST /api/v1/auth/login`.
4. Нормализовать ожидаемый ответ `GET /api/v1/auth/me`.
5. Описать WebSocket endpoint, способ передачи токена и формат realtime-событий.
6. Зафиксировать reconnect/backoff и правило `reloadFeatures(..., force=true)` после восстановления соединения.
7. Записать явный список out-of-scope: create-flow новой feature, все geometry types на frontend, history, analytics, `Project`.
8. Зафиксировать Definition of Done Sprint 1 и demo-сценарий приёмки.

## Только Sprint-1 изменения публичных контрактов

### Входят в Sprint 1

- Новый endpoint `POST /api/v1/auth/login`.
- Нормализация ответа `GET /api/v1/auth/me` под единый пользовательский контракт.
- WebSocket endpoint `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`.
- Realtime payload'ы `feature_created`, `feature_updated`, `feature_deleted`.
- Клиентское правило reconnect с повторной подпиской и принудительной синхронизацией активного слоя.

### Не входят в Sprint 1

- Изменения контрактов CRUD endpoints слоя и feature, кроме их использования в integration-тестах.
- Новый публичный endpoint истории вида `GET /features/{id}/history`.
- Любые аналитические endpoints.
- Публичный контракт create-flow новой feature через UI.
- Публичный контракт frontend-редактирования всех поддерживаемых geometry types.
- Изменения доменной модели и API вокруг сущности `Project`.

### Правило отсечения Sprint 2+

- Если изменение относится к create-flow, all-geometry editing, history, analytics или `Project`, оно не включается в Sprint 1 contract baseline, даже если присутствует в общих требованиях MVP.
- Sprint 1 меняет только auth и realtime contracts, необходимые для demo-сценария совместного редактирования и integration-проверок.

## Контракты

### `POST /api/v1/auth/login`

- Request body:
  - `email`
  - `password`
- Response body:
  - `access_token`
  - `token_type`
  - `user { id, email, role }`
- Ошибки:
  - `401 Unauthorized` при неверных credentials

### `GET /api/v1/auth/me`

- Response body:
  - `user { id, email, role }`
- Ошибки:
  - `401 Unauthorized` при невалидном или отсутствующем токене

### `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`

- Одно соединение соответствует одной подписке на один слой.
- JWT передаётся в query parameter `token`.
- Сервер публикует события:
  - `feature_created`: `eventId`, `occurredAt`, `layerId`, `feature`
  - `feature_updated`: `eventId`, `occurredAt`, `layerId`, `feature`
  - `feature_deleted`: `eventId`, `occurredAt`, `layerId`, `featureId`

## Reconnect Rules

- При разрыве соединения клиент запускает reconnect с backoff.
- После переподключения клиент заново подписывается на активный слой.
- После успешной переподписки клиент выполняет принудительную синхронизацию активного слоя через `reloadFeatures(..., force=true)`.
- Повторная доставка события не должна ломать `tile-cache` или приводить к неконсистентному состоянию карты.

## In Scope для Sprint 1

- Production-ready login flow на `email + password`.
- Нормализованный `GET /api/v1/auth/me` для восстановления сессии.
- WebSocket realtime по активному слою.
- Realtime-события `feature_created`, `feature_updated`, `feature_deleted`.
- Integration-тесты на auth, protected CRUD и базовый realtime-сценарий.

## Out of Scope для Sprint 1

- Create-flow новой feature через UI.
- Frontend-редактирование всех поддерживаемых geometry types.
- История изменений и audit trail.
- Геоаналитика.
- Добавление сущности `Project` в доменную модель.

## Demo-сценарий приёмки Sprint 1

1. Пользователь A и пользователь B входят в систему по `email + password`.
2. Оба клиента открывают один и тот же слой.
3. Пользователь A изменяет объект и успешно сохраняет его.
4. Пользователь B видит изменение по WebSocket почти сразу, без полной перезагрузки приложения.
5. Если пользователь B пытается сохранить устаревшую версию объекта, backend возвращает `409`, а клиент перезагружает актуальное состояние feature.

## Definition of Done для Дня 1

- Все контракты и границы Sprint 1 зафиксированы в markdown.
- Формулировки не противоречат [geoservice-prd-v1.md](/C:/Repositories/geoservice/docs/requirements/geoservice-prd-v1.md), [geoservice-requirements.md](/C:/Repositories/geoservice/docs/requirements/geoservice-requirements.md) и [requirements-compliance-audit.md](/C:/Repositories/geoservice/docs/requirements/requirements-compliance-audit.md).
- По документу можно реализовывать backend и frontend без дополнительных продуктовых решений по Sprint 1.
