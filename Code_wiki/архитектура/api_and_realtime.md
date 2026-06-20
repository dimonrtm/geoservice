---
title: API And Realtime Contracts
type: api-endpoint
status: active
created: 2026-05-30
updated: 2026-06-20
source: repository-change:2026-06-20
tags: [api, websocket, realtime, auth]
---

# API And Realtime Contracts

Backend публикует REST API под `/api/v1` и WebSocket endpoint для layer realtime.

## Auth API

- `POST /api/v1/auth/login` принимает email/password и возвращает `access_token`, `token_type` и user DTO.
- `GET /api/v1/auth/me` возвращает текущего пользователя по Bearer token.
- `POST /api/v1/auth/dev-login` доступен только при `DEV_MODE=true`.

Frontend хранит token в `localStorage`, добавляет `Authorization: Bearer ...` в axios interceptor и вызывает logout при HTTP 401.

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
  все его features и associations, а также все пространственно пересекающиеся
  AOI.
- `feederId` является UUID primary key; неизвестный feeder возвращает
  structured `404 FEEDER_NOT_FOUND`, невалидный UUID - стандартный FastAPI
  `422`.
- Endpoint требует активного `Editor`; `Reviewer` получает
  `403 ROLE_NOT_ALLOWED`.
- Response использует GeoJSON `FeatureCollection` для `network` и `aois`;
  публичные keys `isActive`, `assetCode`, `featureType`, `fromFeatureId`,
  `toFeatureId`, `associationType` сериализуются в camelCase.

## Work Orders API

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

## Ошибки

- Auth errors возвращают `code`, `message`, `correlationId`, `details`; активные
  коды Дня 2: `AUTH_REQUIRED`, `USER_INACTIVE`, `ROLE_NOT_ALLOWED`.
- Utility read errors используют тот же structured contract; повреждённый
  aggregate возвращает `500 UTILITY_DATASET_INVALID`.
- Work Orders errors используют structured contract `code`, `message`,
  `correlationId`, `details`: `WORK_ORDER_NOT_FOUND` для отсутствующего или
  чужого work order, `WORK_ORDER_CONTEXT_INVALID` для рассинхрона work order и
  edit version, `WORK_ORDER_STATE_CONFLICT` для несовместимого статуса.
- Domain validation возвращает 422 с `{"error": "..."}`.
- Missing layer/feature возвращает 404.
- Version conflict возвращает 409 с телом `VERSION_MISMATCH`, `featureId`, `requestVersion`, `currentVersion`, `message`.

## WebSocket Realtime

Endpoint: `GET /api/v1/ws/layers/{layer_id}?token=...`.

Server-side:

- token проверяется через тот же JWT decode и перечитывание user из БД;
- роли `editor` и `reviewer` допускаются к read-only подписке;
- inactive user и legacy/unsupported token role отклоняются с policy violation;
- подписки группируются по `layer_id` в `WebSocketConnectionManager`;
- feature create/update/delete публикуют события `feature_created`, `feature_updated`, `feature_deleted`.

Client-side:

- `useLayerRealtime` строит `ws://` или `wss://` из `VITE_API_BASE_URL`;
- событие `connected` переводит badge в connected-state;
- при reconnect frontend вызывает forced reload активного слоя, чтобы синхронизировать состояние после разрыва.

## Связанные Ноды

- [[backend]]
- [[frontend]]
- [[data_model]]
