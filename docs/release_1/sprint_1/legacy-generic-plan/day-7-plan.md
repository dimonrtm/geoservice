# День 7: публикация realtime-событий после commit CRUD-операций

## Summary

Целевой файл плана: `docs/release_1/sprint_1/legacy-generic-plan/day-7-plan.md`.

Day 7 должен встроить публикацию realtime-событий в backend CRUD-поток для feature без изменения публичных HTTP endpoint'ов. Основа уже подготовлена в Day 6: есть `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`, in-memory connection manager, JWT-аутентификация сокета и handshake `connected`. Вне Day 7 остаются frontend WebSocket client, reconnect-логика на клиенте и integration-сценарий двух реальных клиентов.

## Цель дня

- Публиковать `feature_created`, `feature_updated`, `feature_deleted` из backend после успешного завершения create/update/delete.
- Гарантировать, что realtime-событие не уходит при rollback, `409 VERSION_MISMATCH`, `404` и любых бизнес-ошибках.
- Не ломать текущий `FeatureService`, его HTTP-контракты и существующие unit-тесты.
- Подготовить backend к Day 8 и Day 12 без введения Redis, брокеров, background workers и отдельной очереди событий.

## Входная база Day 7

- Day 6 уже дал:
  - [ws_layers.py](/C:/Repositories/geoservice/apps/backend/app/api/ws_layers.py)
  - [websocket_auth.py](/C:/Repositories/geoservice/apps/backend/app/api/websocket_auth.py)
  - [realtime_connection_manager.py](/C:/Repositories/geoservice/apps/backend/app/services/realtime_connection_manager.py)
- Текущий CRUD feature работает через [feature_service.py](/C:/Repositories/geoservice/apps/backend/app/services/feature_service.py) и транзакции `async with self.session.begin():`.
- Для payload уже есть backend-модели:
  - [FeatureOut](/C:/Repositories/geoservice/apps/backend/app/schemas/feature_out.py)
  - [DeleteFeatureResponse](/C:/Repositories/geoservice/apps/backend/app/schemas/delete_feature_response.py)
- Sprint 1 contract уже фиксирует три event type:
  - `feature_created`
  - `feature_updated`
  - `feature_deleted`

## Результат дня

- После успешного `create_feature(...)` backend публикует `feature_created`.
- После успешного `update_feature(...)` backend публикует `feature_updated`.
- После успешного `delete_feature(...)` backend публикует `feature_deleted`.
- Событие отправляется только после успешного завершения mutate-операции и не публикуется при ошибке.
- Payload соответствует Sprint 1 contract:
  - `type`
  - `eventId`
  - `occurredAt`
  - `layerId`
  - `feature` или `featureId`
- Реализация не меняет response body существующих HTTP CRUD endpoint'ов.

## Ключевое решение

- Day 7 не должен пытаться внедрять SQLAlchemy `after_commit` listener или отдельную event bus-подсистему.
- Для текущей архитектуры проекта достаточно явного service-level orchestration:
  - внутри `FeatureService` mutation сначала формирует доменный результат;
  - после успешного выхода из `async with self.session.begin():` сервис вызывает отдельный realtime publisher;
  - publisher сериализует payload и отправляет его в `WebSocketConnectionManager.broadcast_to_layer(...)`.
- Такой подход:
  - сохраняет простую структуру кода;
  - делает правило post-commit явным;
  - легко покрывается unit-тестами без реальной БД и без Redis.
- Delivery-модель Day 7 является best-effort:
  - успешный CRUD не откатывается, если публикация websocket-события сломалась уже после commit;
  - ошибка доставки не превращается в `500` для HTTP-клиента.

## Задачи

1. Добавить отдельный backend publisher/service для realtime feature-событий.
2. Зафиксировать формат payload для `feature_created`, `feature_updated`, `feature_deleted`.
3. Добавить генерацию `eventId` для каждого исходящего события.
4. Добавить `occurredAt` в формате ISO 8601 UTC с суффиксом `Z`.
5. Подключить publisher к `FeatureService`, не меняя shape текущих CRUD-ответов.
6. Перенести отправку события за пределы transaction-block в `create_feature(...)`.
7. Перенести отправку события за пределы transaction-block в `update_feature(...)`.
8. Перенести отправку события за пределы transaction-block в `delete_feature(...)`.
9. Не публиковать событие, если create/update/delete завершились исключением.
10. Не публиковать событие при `VersionMismatchException`, `FeatureNotFoundException`, `LayerNotFoundException` и `BusinessValidationException`.
11. Добавить dependency/wiring publisher-а так, чтобы он использовал уже существующий `WebSocketConnectionManager`.
12. Обновить unit-тесты `FeatureService` и добавить тесты на publisher payload.

## Решение по реализации

### Publisher слой

- Создать отдельный service, например:
  - `FeatureRealtimePublisher`
- Базовый интерфейс:
  - `publish_feature_created(layer_id, feature)`
  - `publish_feature_updated(layer_id, feature)`
  - `publish_feature_deleted(layer_id, feature_id)`
- Внутри publisher:
  - генерировать `eventId` в формате `evt_<uuid>`
  - формировать `occurredAt` в UTC в ISO 8601 формате с `Z` на конце
  - вызывать `broadcast_to_layer(layer_id, payload)`

### Формат payload

#### `feature_created`

- `type: "feature_created"`
- `eventId: string`
- `occurredAt: string`
- `layerId: string`
- `feature: FeatureOut`
- `feature` отправляется целиком как текущий `FeatureOut`, включая `type: "Feature"`

#### `feature_updated`

- `type: "feature_updated"`
- `eventId: string`
- `occurredAt: string`
- `layerId: string`
- `feature: FeatureOut`
- `feature` отправляется целиком как текущий `FeatureOut`, включая `type: "Feature"`

#### `feature_deleted`

- `type: "feature_deleted"`
- `eventId: string`
- `occurredAt: string`
- `layerId: string`
- `featureId: string`

### Встраивание в `FeatureService`

- В `create_feature(...)`:
  - внутри транзакции получить `FeatureOut`
  - после выхода из `async with self.session.begin():` опубликовать `feature_created`
  - вернуть тот же `FeatureOut`
- В `update_feature(...)`:
  - внутри транзакции получить итоговый `FeatureOut`
  - после выхода из транзакции опубликовать `feature_updated`
  - вернуть тот же `FeatureOut`
- В `delete_feature(...)`:
  - внутри транзакции подтвердить удаление и сохранить `feature_id`
  - после выхода из транзакции опубликовать `feature_deleted`
  - вернуть тот же `DeleteFeatureResponse`

### Правило post-commit

- Публикация должна происходить только после успешного выхода из transaction context.
- Если внутри транзакции выброшено исключение:
  - publisher не вызывается
  - событие в websocket не уходит
- Если `broadcast_to_layer(...)` завершится ошибкой:
  - CRUD-ответ пользователю не должен откатываться задним числом
  - Day 7 должен безопасно проглатывать ошибку доставки как best-effort realtime
  - источник истины остаётся HTTP API и последующий reload/reconnect
  - отдельный logging-слой для этой ошибки в Day 7 не обязателен

### Wiring

- Не создавать отдельный router или новый app state.
- Использовать уже существующий `WebSocketConnectionManager` из Day 6.
- Добавить dependency для publisher в [deps.py](/C:/Repositories/geoservice/apps/backend/app/api/deps.py).
- Обновить создание `FeatureService`, чтобы он получал publisher dependency.

## Ограничения дня

- Без frontend WebSocket client.
- Без reconnect/backoff на клиенте.
- Без Redis, Kafka, RabbitMQ и других внешних брокеров.
- Без persistent event log.
- Без replay-событий при новом подключении.
- Без доставки истории изменений новому клиенту.
- Без изменения HTTP-контрактов create/update/delete.
- Без integration-suite на двух реальных websocket-клиентах; это остаётся на последующие дни.

## Проверки

### Publisher tests

- `publish_feature_created(...)` формирует payload с `feature_created`.
- `publish_feature_updated(...)` формирует payload с `feature_updated`.
- `publish_feature_deleted(...)` формирует payload с `feature_deleted`.
- `layerId`, `featureId`, `eventId`, `occurredAt` сериализуются в строковом формате.
- `eventId` имеет формат `evt_<uuid>`.
- `occurredAt` оканчивается на `Z` и отражает UTC-время.

### Feature service tests

- После успешного `create_feature(...)` publisher вызывается один раз.
- После успешного `update_feature(...)` publisher вызывается один раз.
- После успешного `delete_feature(...)` publisher вызывается один раз.
- При ошибке create/update/delete publisher не вызывается.
- При `VersionMismatchException` publisher не вызывается.
- При `FeatureNotFoundException` publisher не вызывается.

### Smoke criteria

- Existing backend tests остаются зелёными.
- Новые realtime unit-тесты зелёные.
- Day 7 не ломает Day 6 websocket connect/disconnect behavior.
- Day 7 не меняет shape HTTP CRUD responses.

## Demo-сценарий дня

1. Backend стартует с уже готовым websocket-router из Day 6.
2. Клиент A и клиент B подключены к одному `layer_id`.
3. Клиент A создаёт feature через HTTP.
4. Backend завершает транзакцию и публикует `feature_created`.
5. Клиент A обновляет feature через HTTP.
6. Backend завершает транзакцию и публикует `feature_updated`.
7. Клиент A удаляет feature через HTTP.
8. Backend завершает транзакцию и публикует `feature_deleted`.
9. При конфликте версии `409` событие не публикуется.

## Definition of Done для Дня 7

- В backend есть отдельный publisher realtime-событий feature-уровня.
- `FeatureService` публикует `feature_created|updated|deleted` только после успешного commit-path.
- Payload соответствует Sprint 1 contract по полям и именам.
- Ошибочные CRUD-сценарии не публикуют realtime-события.
- Текущий HTTP CRUD API не изменён по контракту.
- Unit-тесты publisher-а и `FeatureService` подтверждают post-commit поведение.

## Assumptions

- Для Day 7 достаточно best-effort доставки внутри одного backend-процесса.
- В Sprint 1 допустимо не гарантировать доставку события при временной проблеме конкретного websocket-соединения.
- Reconnect и принудительная синхронизация на клиенте закроют возможные пропуски доставки.
- `FeatureOut` используется как canonical payload для `feature_created` и `feature_updated` без отдельной realtime-схемы.
- В Day 7 достаточно безопасно проглатывать ошибки websocket-доставки без отдельного logging-механизма.
