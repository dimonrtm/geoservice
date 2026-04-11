# Спринт 1 на 14 дней: закрытие MVP-gap’ов по realtime, auth и integration tests

## Summary

- По коду проект уже имеет рабочие `JWT`, роли `viewer/editor`, защищённые CRUD-эндпойнты, tile-cache и клиентские хуки для локального обновления карты, но у него нет production-login, WebSocket realtime и integration-покрытия.
- Цель спринта 1: сделать воспроизводимый demo-сценарий “два клиента редактируют один слой”, где вход идёт не через `dev-login`, изменения прилетают почти сразу, а auth/protected CRUD защищены интеграционными тестами и CI.
- Вне scope этого спринта: create-flow новой feature через UI, frontend-редактирование всех geometry types, history/audit, аналитика, сущность `Project`.

## Публичные контракты и архитектурные решения

- Добавить `POST /api/v1/auth/login` с `email + password`, ответом `access_token`, `token_type`, `user{id,email,role}`.
- Оставить `GET /api/v1/auth/me`, но нормализовать его под тот же пользовательский контракт, чтобы frontend мог восстанавливать сессию.
- Оставить `POST /api/v1/auth/dev-login` только при `DEV_MODE=true`; dev-панель не удалять, а ограничить dev-сценарием.
- WebSocket сделать через `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`; подписка идёт на один слой на соединение.
- События WebSocket фиксировать в формате:
  - `feature_created` и `feature_updated`: полный `feature` + `layerId` + `eventId` + `occurredAt`
  - `feature_deleted`: `featureId` + `layerId` + `eventId` + `occurredAt`
- Публикацию realtime-событий делать после успешного коммита CRUD-операции в backend service-слое через отдельный publisher/connection manager.
- В production-режиме запретить запуск backend с дефолтным `JWT_SECRET`; refresh token в спринт 1 не включать.
- Для demo/local окружения добавить явный seed-поток предсозданных пользователей с email/password, чтобы login был воспроизводим через `docker-compose`.
- В Sprint 1 не менять публичные контракты history, analytics, `Project`, create-flow новой feature и all-geometry editing на frontend; эти темы остаются за пределами sprint baseline.

### Контракт `POST /api/v1/auth/login`

Назначение:
- Выполняет production-ready login по `email + password` и возвращает JWT для дальнейшего доступа к защищённым endpoint'ам.

Request:
- Method: `POST`
- Path: `/api/v1/auth/login`
- Headers:
  - `Content-Type: application/json`
- Body:
  - `email`: `string`, обязательное поле
  - `password`: `string`, обязательное поле

Пример request body:

```json
{
  "email": "editor@example.com",
  "password": "editor-password"
}
```

Response `200 OK`:
- `access_token`: `string`
- `token_type`: `string`, фиксированное значение `bearer`
- `user`: `object`
- `user.id`: `string`
- `user.email`: `string`
- `user.role`: `"viewer" | "editor"`

Пример response body:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "3c6c5f41-4d2a-4d5a-8b58-2f7a4d59c8a1",
    "email": "editor@example.com",
    "role": "editor"
  }
}
```

Ошибки:
- `401 Unauthorized` при неверных credentials
- `422 Unprocessable Entity` при невалидном JSON или отсутствии обязательных полей

Пример `401 Unauthorized`:

```json
{
  "detail": "Invalid email or password"
}
```

Правила контракта:
- Endpoint не возвращает refresh token в Sprint 1.
- JWT используется дальше как `Authorization: Bearer <access_token>`.
- Контракт login не зависит от `DEV_MODE`; `dev-login` остаётся отдельным dev-only endpoint.

### Контракт `GET /api/v1/auth/me`

Назначение:
- Возвращает текущего авторизованного пользователя по переданному JWT и используется frontend для восстановления сессии после перезагрузки приложения.

Request:
- Method: `GET`
- Path: `/api/v1/auth/me`
- Headers:
  - `Authorization: Bearer <access_token>`

Response `200 OK`:
- `user`: `object`
- `user.id`: `string`
- `user.email`: `string`
- `user.role`: `"viewer" | "editor"`

Пример response body:

```json
{
  "user": {
    "id": "3c6c5f41-4d2a-4d5a-8b58-2f7a4d59c8a1",
    "email": "editor@example.com",
    "role": "editor"
  }
}
```

Ошибки:
- `401 Unauthorized` при отсутствии токена
- `401 Unauthorized` при невалидном или протухшем токене

Пример `401 Unauthorized`:

```json
{
  "detail": "Invalid or expired token"
}
```

Правила контракта:
- Ответ `GET /api/v1/auth/me` должен быть нормализован под тот же объект `user`, что и `POST /api/v1/auth/login`.
- В Sprint 1 endpoint не должен возвращать разрозненные поля вида `user_id` и `user_role`.
- Endpoint не изменяет состояние пользователя и используется только для чтения текущей сессии.

### Контракт `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`

Назначение:
- Обеспечивает realtime-подписку на изменения одного слоя и доставляет события `feature_created`, `feature_updated`, `feature_deleted` второму клиенту почти в реальном времени.

Подключение:
- Protocol: `ws` или `wss`
- Path: `/api/v1/ws/layers/{layer_id}`
- Path params:
  - `layer_id`: `string`
- Query params:
  - `token`: `string`, обязательный JWT access token

Правило подключения:
- Одно WebSocket-соединение соответствует одной подписке на один `layer_id`.
- JWT передаётся через query parameter `token`.
- Если токен отсутствует, невалиден или истёк, сервер отклоняет подключение.

Поведение авторизации:
- Для успешной подписки клиент должен передавать тот же access token, который получил через `POST /api/v1/auth/login`.
- Роль `viewer` может подписываться на realtime-события чтения.
- Роль `editor` может подписываться на realtime-события и параллельно выполнять mutate-операции через HTTP API.

### Формат realtime-событий

Общие поля каждого события:
- `type`: `string`
- `eventId`: `string`
- `occurredAt`: `string` в формате ISO 8601
- `layerId`: `string`

#### Событие `feature_created`

```json
{
  "type": "feature_created",
  "eventId": "evt_01hrx3x9x9z6m2v8h3j4q1k7aa",
  "occurredAt": "2026-04-11T18:45:12Z",
  "layerId": "6b2e1f52-0a58-4f4d-bf7d-8d4e16a8db61",
  "feature": {
    "id": "3c6c5f41-4d2a-4d5a-8b58-2f7a4d59c8a1",
    "version": 1,
    "properties": {
      "name": "New feature"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[10.0, 10.0], [20.0, 10.0], [20.0, 20.0], [10.0, 10.0]]]
    }
  }
}
```

Правило обработки:
- Клиент выполняет `upsert` feature в cache/source.

#### Событие `feature_updated`

```json
{
  "type": "feature_updated",
  "eventId": "evt_01hrx3y8s8n1k3r7m2a4p9d5bb",
  "occurredAt": "2026-04-11T18:46:03Z",
  "layerId": "6b2e1f52-0a58-4f4d-bf7d-8d4e16a8db61",
  "feature": {
    "id": "3c6c5f41-4d2a-4d5a-8b58-2f7a4d59c8a1",
    "version": 2,
    "properties": {
      "name": "Updated feature"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[10.0, 10.0], [25.0, 10.0], [25.0, 25.0], [10.0, 10.0]]]
    }
  }
}
```

Правило обработки:
- Клиент выполняет `upsert`, инвалидирует затронутые tiles и синхронизирует source без полной перезагрузки приложения.

#### Событие `feature_deleted`

```json
{
  "type": "feature_deleted",
  "eventId": "evt_01hrx3z7f4j7n9q2k6p3m8c1cc",
  "occurredAt": "2026-04-11T18:47:40Z",
  "layerId": "6b2e1f52-0a58-4f4d-bf7d-8d4e16a8db61",
  "featureId": "3c6c5f41-4d2a-4d5a-8b58-2f7a4d59c8a1"
}
```

Правило обработки:
- Клиент удаляет feature из cache/source и синхронизирует видимый слой.

### Правила доставки и идемпотентности

- События публикуются только после успешного завершения create/update/delete операции.
- Повторная доставка одного и того же события не должна ломать состояние клиента.
- Поле `eventId` используется как идентификатор события для отладки и возможной дедупликации на клиенте.
- Источником истины для актуального состояния feature остаётся backend API.

### Правила reconnect

- После разрыва соединения клиент запускает reconnect с backoff.
- После переподключения клиент повторно открывает соединение на тот же `layer_id` и повторно передаёт `token`.
- После успешного reconnect клиент выполняет принудительную синхронизацию активного слоя через `reloadFeatures(..., force=true)`.
- Reconnect не добавляет новые публичные event types в Sprint 1; он опирается на тот же контракт событий.

## План по дням

1. День 1: зафиксировать contracts спринта 1. Описать login/WS/event payload, reconnect-поведение, out-of-scope спринта и DoD в `docs/`.
2. День 2: усилить backend auth-конфигурацию. Добавить валидацию `JWT_SECRET`, подготовить login-схемы, сервис проверки пароля и политику разделения `dev-login` и normal login.
3. День 3: реализовать backend login flow. Добавить поиск пользователя с `password_hash`, проверку пароля, выдачу JWT, нормализованный `/me`, негативные ответы `401`.
4. День 4: добавить seed demo-пользователей для compose/demo-сценария и обновить запуск, чтобы локально можно было войти без `dev-login`.
5. День 5: внедрить frontend login flow. Отрисовывать login-экран при отсутствии токена, хранить пользователя в auth-store, оставить dev-auth panel только под `VITE_ENABLE_DEV_AUTH`.
6. День 6: подготовить backend realtime-ядро. Добавить websocket-router, JWT-аутентификацию сокета, connection manager по `layer_id`, lifecycle-хуки на connect/disconnect.
7. День 7: встроить публикацию realtime-событий в create/update/delete feature и гарантировать, что событие уходит только после успешного коммита.
8. День 8: реализовать frontend WebSocket client для активного слоя, обработку reconnect/backoff и принудительный `reloadFeatures(..., force=true)` после восстановления соединения.
9. День 9: связать входящие WS-события с существующим tile-cache. Для `create/update` использовать `upsert + invalidate/reload`, для `delete` — `remove + sync`, без полной перезагрузки приложения.
10. День 10: покрыть frontend unit-тестами auth-store/login-flow и обработчик realtime-событий, включая идемпотентность повторной доставки.
11. День 11: добавить backend integration-тесты на auth. Проверить успешный login, неверный пароль, `401` без токена, `403` для `viewer` на mutate-операциях.
12. День 12: добавить backend integration-тесты на protected CRUD и realtime. Проверить `editor` create/update/delete, публикацию `feature_created|updated|deleted`, базовый сценарий двух клиентов.
13. День 13: встроить integration-suite в CI, обновить compose/demo-документацию, прогнать demo-checklist и устранить регрессии.
14. День 14: стабилизация и приёмка. Финальный проход по DoD, smoke demo “A редактирует, B видит, B получает `409` на устаревшей версии”, фиксация известных ограничений и handoff-заметок для спринта 2.

## Test Plan

- Backend integration:
  - login success/fail
  - `401` на protected routes без токена
  - `403` для `viewer` на `POST/PATCH/DELETE`
  - `editor` может выполнить create/update/delete
  - websocket-клиент получает `feature_created`, `feature_updated`, `feature_deleted`
- Frontend automated:
  - auth-store сохраняет/сбрасывает токен и пользователя
  - login screen переключает приложение в карту после успешного входа
  - realtime-обработчик не ломается на повторной доставке события
  - reconnect инициирует повторную синхронизацию активного слоя
- Acceptance/demo:
  - два клиента входят по email/password
  - клиент B видит изменение клиента A за `1–2 секунды`
  - конфликт версии по-прежнему даёт `409` и не теряет данные
  - CI остаётся зелёным без добавления e2e-браузерного контура в этом спринте

## Demo-сценарий приёмки Sprint 1

1. Пользователь A входит в систему через `POST /api/v1/auth/login` и открывает нужный слой.
2. Пользователь B входит в систему через `POST /api/v1/auth/login` и открывает тот же слой.
3. Оба клиента устанавливают realtime-подписку через `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`.
4. Пользователь A изменяет существующую feature и успешно сохраняет её через HTTP API.
5. Пользователь B получает событие `feature_updated` почти сразу, без ручной перезагрузки приложения.
6. Пользователь B начинает редактирование на устаревшей версии feature и пытается сохранить изменения.
7. Backend возвращает `409 VERSION_MISMATCH`.
8. Клиент B перезагружает актуальное состояние feature и позволяет повторить редактирование уже с актуальной версией.
9. Integration-проверки на auth, protected CRUD и realtime остаются зелёными.

## Definition of Done Sprint 1

- Реализован `POST /api/v1/auth/login` с контрактом, зафиксированным в этом плане.
- `GET /api/v1/auth/me` нормализован и возвращает единый объект `user { id, email, role }`.
- `POST /api/v1/auth/dev-login` остаётся доступным только в `DEV_MODE=true` и не используется как основной production-login flow.
- Реализован `WS /api/v1/ws/layers/{layer_id}?token=<jwt>` для подписки на один слой.
- Backend публикует события `feature_created`, `feature_updated`, `feature_deleted` только после успешного завершения mutate-операций.
- Frontend принимает realtime-события, обновляет cache/source и не требует полной перезагрузки приложения для демонстрационного сценария.
- После разрыва соединения клиент может переподключиться, повторно подписаться на активный слой и выполнить повторную синхронизацию.
- Есть integration-тесты на login success/fail, `401`, `403`, protected CRUD и базовый realtime-сценарий двух клиентов.
- Demo/local окружение позволяет войти по `email + password` без зависимости от `dev-login`.
- CI остаётся зелёным после добавления auth и realtime изменений.
- В Sprint 1 не добавлены публичные контракты history, analytics, `Project`, create-flow новой feature и all-geometry editing на frontend.

## Assumptions

- Зафиксирован целевой auth-flow: `email + password`, без внешнего SSO.
- Seed-пользователи нужны только для demo/local воспроизводимости; полноценный user-management не входит в спринт 1.
- Спринт планируется как один последовательный поток реализации без параллельной команды.
- Оценка опирается на код-ревью текущего репозитория и документы `docs/`; локальный полный прогон существующих тестов в этой среде не был надёжно подтверждён.
