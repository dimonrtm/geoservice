# День 6: backend realtime-ядро и WebSocket-подписка по слою

## Summary

Целевой файл плана: `docs/requirements/sprints/sprint-1/day-6-plan.md`.

Day 6 должен подготовить backend realtime-ядро без публикации CRUD-событий: добавить WebSocket endpoint для подписки на один слой, JWT-аутентификацию сокета, in-memory connection manager по `layer_id` и lifecycle-хуки на connect/disconnect. Вне Day 6 остаются сами `feature_created|updated|deleted` публикации, frontend WebSocket client и integration-сценарий двух клиентов.

## Key Changes

- Добавить backend endpoint `WS /api/v1/ws/layers/{layer_id}?token=<jwt>` в отдельном websocket-router и подключить его в `main.py`.
- Вынести JWT-проверку для WebSocket в отдельный auth helper, использующий уже существующий JWT contract Sprint 1.
- Ввести in-memory `connection manager`, который:
  - хранит активные соединения по `layer_id`
  - поддерживает `connect`, `disconnect`, `broadcast_to_layer`
  - не требует Redis или внешнего брокера в Day 6
- Расширить `lifespan` так, чтобы manager жил на уровне приложения и был доступен через dependency/app state.
- Зафиксировать handshake-поведение:
  - токен обязателен в query param `token`
  - одно соединение соответствует одному `layer_id`
  - `viewer` и `editor` могут подписываться на чтение realtime
  - невалидный токен или несуществующий слой приводят к отказу в подключении
- Day 6 не меняет `FeatureService` и не публикует события из CRUD; он только готовит инфраструктуру для Day 7.

## Implementation Changes

### WebSocket router

- Создать отдельный backend router для WebSocket, а не встраивать endpoint в существующий `layers_router`.
- Endpoint должен:
  - принимать `layer_id`
  - читать `token` из query params
  - валидировать JWT тем же секретом и алгоритмом, что и HTTP auth
  - проверять, что `sub` и `role` присутствуют в payload
  - проверять, что пользователь из токена существует в БД
  - при необходимости проверять, что слой существует
  - принимать соединение только после успешной аутентификации и валидации слоя

### Connection manager

- Реализовать in-memory manager уровня процесса.
- Базовый интерфейс:
  - `connect(layer_id, websocket, user_context)`
  - `disconnect(layer_id, websocket)`
  - `broadcast_to_layer(layer_id, event)`
  - `get_connection_count(layer_id)` для отладки/тестов
- Ключ хранения: `layer_id`.
- Одно соединение подписано ровно на один слой.
- Manager должен быть устойчив к повторному `disconnect` и к разрыву соединения без дополнительной ошибки.

### Auth и dependencies

- Не дублировать auth-логику из HTTP-роутов напрямую в endpoint.
- Вынести websocket-friendly helper для:
  - decode JWT
  - нормализации ошибок аутентификации сокета
  - извлечения пользователя по `sub`
- User context для соединения должен минимум содержать:
  - `user_id`
  - `email`
  - `role`

### Lifecycle и app wiring

- Создать manager в `lifespan` и положить его в `app.state`.
- Добавить dependency для получения manager из `app.state`.
- Подключить websocket-router в `main.py`.
- Day 6 не требует специальных shutdown-сценариев кроме штатной очистки in-memory соединений вместе с завершением процесса.

### Contract и поведение подключения

- Успешный Day 6 даёт только инфраструктуру соединения, без обязательного server push payload.
- Разрешено после успешного подключения отправлять техническое acknowledgement-сообщение вида `connected`, если это нужно для дебага и тестов.
- Если acknowledgement вводится, оно должно быть явно техническим и не смешиваться с контрактом `feature_created|updated|deleted`, который появится только в Day 7.
- Ошибки подключения для Day 6:
  - без токена: отказ в подключении
  - невалидный/просроченный токен: отказ в подключении
  - пользователь не найден: отказ в подключении
  - слой не найден: отказ в подключении
- В Day 6 не добавлять новые env vars, Redis, background workers или persistent subscription storage.

## Test Plan

- Unit tests на connection manager:
  - регистрация соединения по `layer_id`
  - удаление соединения
  - устойчивость к повторному `disconnect`
  - broadcast по конкретному слою не затрагивает другие слои
- Auth tests на websocket helper:
  - валидный токен даёт user context
  - невалидный токен отклоняется
  - отсутствующий `sub` или `role` отклоняется
  - пользователь из токена не найден
- Route-level tests на websocket endpoint:
  - успешное подключение `viewer`
  - успешное подключение `editor`
  - отказ без `token`
  - отказ с невалидным токеном
  - отказ для несуществующего `layer_id`
- Smoke criteria для Day 6:
  - backend стартует с подключённым websocket-router
  - клиент может открыть и закрыть `WS /api/v1/ws/layers/{layer_id}?token=<jwt>` без падения backend
  - Day 6 не ломает существующие HTTP auth и CRUD routes

## Assumptions

- Day 6 использует in-memory manager в одном backend-процессе; multi-instance delivery не входит в Sprint 1 baseline.
- Подписка на realtime разрешена ролям `viewer` и `editor`; write-права остаются HTTP-only.
- Проверка существования слоя нужна уже на этапе подключения, чтобы не держать подписки на невалидные `layer_id`.
- Публикация `feature_created|updated|deleted` и post-commit orchestration остаются задачей Day 7.
- План рассчитан на текущую структуру backend: отдельные `api/`, `services/`, `deps`, `lifespan`, без архитектурного рефактора перед внедрением WebSocket.
