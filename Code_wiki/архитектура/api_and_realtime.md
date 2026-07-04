---
title: API And Realtime Contracts
type: api-endpoint
status: active
created: 2026-05-30
updated: 2026-07-03
source: repository-change:2026-07-03
tags: [api, websocket, realtime, auth]
---

# API And Realtime Contracts

Backend публикует REST API под `/api/v1` и WebSocket endpoint для layer realtime.

## Auth API

- `POST /api/v1/auth/login` принимает email/password, возвращает
  short-lived Bearer `access_token`, `token_type` и user DTO, а долгую
  auth-сессию кладет только в HttpOnly cookie `geoservice_session`.
- Auth session cookie ограничена `Path=/api/v1/auth`; raw session token не
  попадает в JSON response и хранится в БД только как SHA-256 hash в
  `user.auth_sessions`. TTL по умолчанию - 12 часов.
- `POST /api/v1/auth/session/refresh` читает session cookie, атомарно
  ротирует active session в БД, ставит новый HttpOnly cookie и возвращает
  новый Bearer `access_token`. Missing/expired/revoked/replayed session
  возвращает structured `401 AUTH_REQUIRED`; inactive user - `403 USER_INACTIVE`.
- `POST /api/v1/auth/logout` идемпотентно отзывает active session по cookie и
  очищает cookie.
- `GET /api/v1/auth/me` возвращает текущего пользователя по Bearer token.

Auth session cookies требуют credentials-enabled CORS. Backend запрещает
wildcard CORS origins, валидирует `AUTH_SESSION_COOKIE_SAMESITE`
(`lax|strict|none`), требует `AUTH_SESSION_COOKIE_SECURE=True` при
`DEV_MODE=false` и не допускает `SameSite=None` без `Secure`.

Frontend не хранит `access_token`/user в `localStorage`: Pinia держит их
только in-memory, `restoreSession()` выполняет cookie refresh, а axios 401
interceptor очищает локальное состояние без дополнительного backend logout.

## Layers And Features API

- `GET /api/v1/layers` возвращает список layers.
- `GET /api/v1/layers/{layer_id}/features?bbox=...&limit=...&after_id=...` возвращает GeoJSON FeatureCollection и `meta`.
- `GET /api/v1/layers/{layer_id}/features/{feature_id}` возвращает одну feature.
- `POST /api/v1/layers/{layer_id}/features` создает feature, требует `editor`.
- `PATCH /api/v1/layers/{layer_id}/features/{feature_id}` обновляет feature по optimistic `version`, требует `editor`.
- `DELETE /api/v1/layers/{layer_id}/features/{feature_id}` удаляет feature по optimistic `version`, требует `editor`.

`bbox` валидируется как четыре числа с диапазонами долготы/широты. `limit` нормализуется backend-ом в диапазон `1..5000`; frontend обычно запрашивает `500`.

## Utility Network API

- `GET /api/v1/utility-network/feeders/{feederId}` возвращает полный feeder,
  все его features и associations. AOI не входит в этот bounded context и
  возвращается через Workspace API.
- `feederId` является UUID primary key; неизвестный feeder возвращает
  structured `404 FEEDER_NOT_FOUND`, невалидный UUID - стандартный FastAPI
  `422`.
- Endpoint требует активного `Editor`; `Reviewer` получает
  `403 ROLE_NOT_ALLOWED`.
- Response использует GeoJSON `FeatureCollection` для `network`;
  публичные keys `isActive`, `assetCode`, `featureType`, `fromFeatureId`,
  `toFeatureId`, `associationType` сериализуются в camelCase.

## Work Orders API

- `GET /api/v1/work-orders/assigned-to-me` возвращает текущему активному
  `Editor` список всех назначенных ему work orders. Endpoint не открывает
  `EditVersion`, не меняет `WorkOrder.status` и нужен для shell `Мои наряды`
  после login.
- Response имеет компактную форму `{ "workOrders": [...] }`, где каждый элемент
  содержит только `id`, `code`, `title`, `description`, `status`; audit/internal
  date fields не публикуются. Backend сортирует список по внутреннему
  `updated_at DESC`, затем `code ASC` для стабильного порядка.
- `POST /api/v1/work-orders/{work_order_id}/edit-versions` открывает edit
  version для назначенного work order текущего `Editor`.
- При первом открытии endpoint создает `EditVersion` как deep copy активного
  `DefaultState` этого work order, переводит work order из `assigned` в
  `in_progress` и возвращает `201` с `created: true`.
- При повторном открытии work order в `in_progress` endpoint возвращает уже
  открытую edit version, обновляет `lastOpenedAt` и отвечает `200` с
  `created: false`.
- Response содержит `editVersion.id`, `workOrderId`, `ownerId`, `status`,
  `baseNetworkRevision`, `createdAt`, `lastOpenedAt`.
- `GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`
  возвращает workspace только для уже существующей открытой edit version и не
  создаёт новую версию, не открывает work order и не меняет `WorkOrder.status`.
  Route вложен в `work-orders/{workOrderId}`, потому что workspace читается из
  агрегата `WorkOrder`.
- Workspace response содержит `workOrder.id`, `code`, `title`, `status`,
  `scope.aoi` с GeoJSON geometry и extent, а также `editVersion.id`, `status`,
  `baseNetworkRevision`, `features` и `associations`. Features берутся из
  `work_order.edit_version_features` и фильтруются по `WorkOrder.scope.aoi`;
  associations попадают в ответ только когда оба endpoint feature входят в
  рабочую область. DTO для workspace features и associations находятся в
  `schemas.workspace` и не реиспользуют output-схемы `utility_network`.

## Ошибки

- `AuthApiError`, `UtilityNetworkApiError` и `WorkOrderApiError` сериализуются
  единым strict structured contract `{code, message, correlationId}` без
  `detail` и `details`. `correlationId` берётся из `X-Correlation-ID`, а при
  отсутствии header генерируется backend-ом.
- Неверные email/password в `POST /api/v1/auth/login` возвращают
  `401 INVALID_CREDENTIALS` с сообщением `Неверная электронная почта или пароль`.
- Остальные активные auth-коды: `AUTH_REQUIRED`, `USER_INACTIVE`,
  `ROLE_NOT_ALLOWED`.
- Utility read errors используют тот же structured contract; повреждённый
  aggregate возвращает `500 UTILITY_DATASET_INVALID`.
- Work Orders errors используют тот же structured contract:
  `WORK_ORDER_NOT_FOUND` для отсутствующего или чужого work order,
  `WORK_ORDER_CONTEXT_INVALID` для рассинхрона work order и edit version,
  `WORK_ORDER_STATE_CONFLICT` для несовместимого статуса.
- Workspace errors используют тот же structured contract: `EDIT_VERSION_NOT_FOUND`
  маскирует отсутствующую, чужую или не связанную с work order edit version,
  `EDIT_VERSION_STATE_CONFLICT` возвращается для неподходящего состояния
  `WorkOrder`/`EditVersion`, `WORKSPACE_CONTEXT_INVALID` означает, что из
  текущих данных нельзя сформировать workspace.
- Domain validation возвращает 422 с `{"error": "..."}`.
- Missing layer/feature возвращает 404.
- Version conflict возвращает 409 с телом `VERSION_MISMATCH`, `featureId`, `requestVersion`, `currentVersion`, `message`.

## WebSocket Realtime

Endpoint для выдачи ticket: `POST /api/v1/ws/layers/{layer_id}/ticket`.
Endpoint подписки: `GET /api/v1/ws/layers/{layer_id}?ticket=...`.

Server-side:

- ticket issue endpoint требует обычный HTTP `Authorization: Bearer ...`;
- raw ticket возвращается только клиенту и хранится в БД только как SHA-256 hash;
- ticket короткоживущий, одноразовый и привязан к `layer_id`;
- WebSocket handshake атомарно consumes ticket через `UPDATE ... used_at IS NULL ... RETURNING`;
- missing/invalid/expired/reused/wrong-layer ticket отклоняется с policy violation `1008`;
- старый `?token=<jwt>` больше не авторизует WebSocket;
- роли `editor` и `reviewer` допускаются к read-only подписке;
- inactive user и unsupported role отклоняются с policy violation;
- подписки группируются по `layer_id` в `WebSocketConnectionManager`;
- feature create/update/delete публикуют события `feature_created`, `feature_updated`, `feature_deleted`.

Client-side:

- `useLayerRealtime` перед каждым initial connect и reconnect получает новый ticket через HTTP API;
- `useLayerRealtime` строит `ws://` или `wss://` из `VITE_API_BASE_URL`;
- WebSocket URL содержит `ticket=...` и не содержит JWT `token=...`;
- событие `connected` переводит badge в connected-state;
- при reconnect frontend вызывает forced reload активного слоя, чтобы синхронизировать состояние после разрыва.

## Связанные Ноды

- [[backend]]
- [[frontend]]
- [[data_model]]
