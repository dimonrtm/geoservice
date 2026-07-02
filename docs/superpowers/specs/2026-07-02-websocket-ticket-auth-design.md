# Замена JWT Query String В WebSocket На Short-Lived Ticket

Дата: 2026-07-02
Статус: design approved
Источник: security backlog по WebSocket query string token

## Контекст

Текущий realtime контракт использует `WS /api/v1/ws/layers/{layer_id}?token=<jwt>`.
Backend в `utility_service.web_api.api.ws_layers` читает JWT из query string,
проверяет его через общий JWT decode и открывает read-only подписку для ролей
`editor` и `reviewer`. Frontend в `useLayerRealtime` строит WebSocket URL с
`token=...`.

Это оставляет полноценный access JWT в URL, который может попасть в browser
history, proxy/server logs, error reports или diagnostics. Обычный browser
`WebSocket` не позволяет выставить `Authorization` header, поэтому безопасная
замена должна дать клиенту другой короткий credential для handshake.

## Цели

- Убрать полноценный JWT из WebSocket URL.
- Сохранить текущий HTTP auth flow: login возвращает Bearer `access_token`,
  frontend хранит его и отправляет `Authorization: Bearer ...` для REST API.
- Добавить short-lived single-use WebSocket ticket, который переживает несколько
  backend-инстансов и рестарты.
- Привязать ticket к конкретному `layer_id` и пользователю.
- Сохранить текущую модель realtime: одно WebSocket-соединение подписано на один
  layer, роли `editor` и `reviewer` могут подписываться, reconnect делает forced
  reload активного слоя после восстановления.
- Удалить поддержку `?token=<jwt>` для WebSocket без backward compatibility.

## Не Цели

- Не переводить весь auth на cookie-based session.
- Не добавлять refresh tokens или новую session модель.
- Не добавлять Redis или другой внешний state store.
- Не менять формат realtime events.
- Не менять authorization rules для layers/features/work orders.

## Выбранный Подход

Выбран DB-backed layer-bound ticket flow:

1. Frontend вызывает `POST /api/v1/ws/layers/{layerId}/ticket` с текущим
   `Authorization: Bearer <access_token>`.
2. Backend проверяет пользователя, роль, активность учетной записи и наличие
   слоя.
3. Backend генерирует cryptographically random opaque ticket, хранит только hash
   ticket в БД и возвращает клиенту raw ticket вместе с `expiresAt`.
4. Frontend сразу открывает `WS /api/v1/ws/layers/{layerId}?ticket=<opaque>`.
5. WebSocket endpoint атомарно consumes ticket в БД: ticket должен существовать,
   быть неиспользованным, неистекшим и привязанным к этому `layer_id`.
6. После успешного consume backend строит `WebSocketUserContext`, принимает
   socket и отправляет `{"type": "connected", "layerId": "..."}`.
7. При reconnect frontend запрашивает новый ticket; старый ticket никогда не
   переиспользуется.

Такой вариант не делает URL полностью credential-free, но credential в URL
становится короткоживущим, одноразовым, layer-bound и не является JWT.

## Альтернативы

### `Sec-WebSocket-Protocol`

Можно передавать ticket через browser WebSocket subprotocol:
`new WebSocket(url, ["geoservice.realtime", "ticket.<opaque>"])`.
Это убирает credential из URL, но делает handshake контракт менее привычным,
требует аккуратного subprotocol negotiation и потенциально сложнее для тестов и
прокси.

### Cookie Auth

Cookie auth для WebSocket убирает credential из URL полностью, но требует
переделки общей auth модели: `HttpOnly`, `SameSite`, CSRF, CORS credentials и
logout semantics. Это больше текущего scope.

### In-Memory Ticket Registry

In-memory registry проще, но не обеспечивает strict single-use при нескольких
backend-инстансах и теряет состояние при рестарте. Этот вариант отклонен.

## Backend Components

- `utility_service.web_api.api.ws_layers`
  - Добавляет `POST /api/v1/ws/layers/{layer_id}/ticket` или подключает
    отдельный router для выдачи tickets.
  - WebSocket route перестает читать `token` и читает `ticket`.
  - Старый `?token=<jwt>` не авторизует соединение.
- Новый helper рядом с текущим `websocket_auth.py`, например
  `websocket_ticket_auth.py`.
  - Converts consumed ticket result в `WebSocketUserContext`.
  - Маппит ticket/auth ошибки в `WebSocketException` с code `1008`.
- Новый use-case service, например `WebSocketTicketService`.
  - `issue_ticket(user, layer_id)` создает ticket для активного
    `editor|reviewer` и существующего слоя.
  - `consume_ticket(ticket, layer_id)` выполняет single-use validation и
    возвращает user context data.
- Новый repository:
  `utility_service.infrastructure.postgresql.repositories.websocket_ticket_repository`.
  - Вставляет ticket row.
  - Атомарно consumes ticket через `UPDATE ... WHERE ticket_hash = ...
    AND layer_id = ... AND used_at IS NULL AND expires_at > now()
    RETURNING ...`.
- Новая SQLAlchemy model и Alembic migration для
  `"user".websocket_tickets`.
- Settings:
  - `WEBSOCKET_TICKET_TTL_SECONDS`, default `60`.

## Data Model

Таблица `"user".websocket_tickets`:

- `id`: UUID primary key.
- `ticket_hash`: string, unique, indexed.
- `user_id`: UUID, user who requested the ticket.
- `layer_id`: UUID, layer for which the ticket is valid.
- `expires_at`: timezone-aware timestamp.
- `used_at`: nullable timezone-aware timestamp.
- `created_at`: timezone-aware timestamp with server default `now()`.

Raw ticket не хранится. Для lookup используется SHA-256 hash от opaque ticket.
Raw ticket должен генерироваться через
cryptographically secure generator, например `secrets.token_urlsafe(32)`.

Индексы:

- unique index на `ticket_hash`;
- index на `expires_at` для будущего cleanup;
- composite index на `(layer_id, expires_at)` не добавляется в MVP, потому что
  lookup идет по `ticket_hash`.

## Data Flow

1. Пользователь логинится как сейчас и получает обычный `access_token`.
2. Когда frontend хочет открыть realtime для слоя, он вызывает
   `POST /api/v1/ws/layers/{layerId}/ticket` с `Authorization: Bearer ...`.
3. Backend проверяет текущего пользователя через `get_current_user`.
4. Ticket service проверяет роль `editor|reviewer`, наличие слоя и создает ticket
   row с TTL.
5. Frontend открывает `WS /api/v1/ws/layers/{layerId}?ticket=...`.
6. Backend consumes ticket атомарным update.
7. Если consume успешен, backend принимает socket и отправляет `connected`.
8. При штатном disconnect ticket не возвращается в доступное состояние.
9. При reconnect frontend повторяет HTTP issue и WebSocket connect с новым
   ticket.

## Errors

HTTP ticket issue endpoint использует текущий strict structured error contract:

- `401 AUTH_REQUIRED` для отсутствующей или недействительной HTTP-сессии.
- `403 USER_INACTIVE` для отключенной учетной записи.
- `403 ROLE_NOT_ALLOWED`, если роль не может подписываться на realtime.
- `404 LAYER_NOT_FOUND` для отсутствующего layer, в том же strict structured
  формате `{code, message, correlationId}`. Это новый auth-adjacent endpoint,
  поэтому он не наследует legacy `{"error": ...}` shape из старых layer feature
  routes.

WebSocket handshake errors закрывают соединение с code `1008`, как сейчас:

- missing ticket;
- invalid ticket;
- expired ticket;
- already used ticket;
- ticket for another layer;
- user no longer exists, inactive, or role no longer allowed.

Причины `invalid`, `expired`, `already used` и `wrong layer` не должны
раскрывать детали клиенту. Для frontend это единая auth-related realtime error,
которая останавливает reconnect.

## Frontend Components

- Новый API module, например `src/api/realtime.ts`.
  - `issueLayerWebSocketTicket(layerId)` вызывает
    `POST /api/v1/ws/layers/{layerId}/ticket`.
- `src/composables/map/useLayerRealtime.ts`.
  - Перед каждым `new WebSocket(...)` получает свежий ticket.
  - Строит URL с `ticket=...`.
  - Больше не строит URL с `token=...`.
  - На reconnect снова вызывает ticket endpoint.
  - Текущий badge/error behavior сохраняется.
- Сигнатура `handleLayerChange(layer, token)` должна быть уточнена так, чтобы
  `useLayerRealtime` больше не принимал JWT как WebSocket credential. Компонент
  передает только layer/auth-ready state, а composable сам вызывает ticket API по
  текущему HTTP auth state через axios interceptor.

## Testing

Backend:

- Ticket issue возвращает raw ticket и `expiresAt` для авторизованного
  `editor|reviewer`.
- Ticket issue отклоняет отсутствующую сессию, inactive user и role not allowed.
- Ticket consume успешен ровно один раз.
- Reused ticket отклоняется.
- Expired ticket отклоняется.
- Ticket for another layer отклоняется.
- Inactive или удаленный user после issue отклоняется на WebSocket consume.
- `WS /api/v1/ws/layers/{layer_id}?ticket=...` открывает соединение и отправляет
  `connected`.
- `WS /api/v1/ws/layers/{layer_id}?token=<jwt>` больше не открывает соединение.

Frontend:

- `useLayerRealtime` вызывает ticket endpoint перед первичным connect.
- URL WebSocket содержит `ticket=...` и не содержит `token=`.
- Reconnect запрашивает новый ticket.
- Auth-related close code `1008` сохраняет текущую остановку reconnect.
- Missing/failed ticket issue не создает WebSocket с пустым или старым ticket.

## Документация

После реализации нужно обновить:

- `Code_wiki/архитектура/api_and_realtime.md`;
- `Code_wiki/архитектура/backend.md`, если будет добавлена новая ticket table и
  service boundary;
- `Code_wiki/архитектура/frontend.md`, если меняется contract `useLayerRealtime`;
- `Code_wiki/правила_и_стиль/testing_strategy.md`, если добавляются новые
  обязательные тесты;
- `docs/agent-memory/file-map.md`, если durable topic-to-file relationship
  меняется и не покрыт Code_wiki.

Repository-change ingest нужен только если реализация создаст новое durable
technical knowledge, которое должно жить в `Code_wiki`. Сам факт выполнения
задачи, список измененных файлов и успешные тесты не являются триггером.

## Критерии Готовности

- WebSocket JWT query string auth удален.
- Short-lived single-use ticket flow работает через БД.
- Ticket привязан к `layer_id`, пользователю и TTL.
- One ticket cannot open two WebSocket connections.
- Reconnect получает новый ticket.
- Existing HTTP Bearer auth flow не меняется.
- Backend и frontend tests покрывают success, missing/invalid/reused/expired
  ticket и отсутствие `token=` в WebSocket URL.
