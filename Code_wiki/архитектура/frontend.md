---
title: Frontend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-06-29
source: repository-change:2026-06-29
tags: [frontend, vue, maplibre, architecture]
---

# Frontend Architecture

Frontend находится в `apps/frontend` и построен на Vue 3, TypeScript, Pinia, Vite и MapLibre GL.

## Входные Точки

- `src/main.ts` подключает MapLibre CSS, общий CSS, Pinia и монтирует `App.vue`.
- `src/App.vue` восстанавливает auth session, показывает `LoginScreen` или role-specific авторизованную страницу: `EditorWorkOrdersView` для `Editor`, reviewer home для `Reviewer`.
- `src/components/EditorWorkOrdersView.vue` является стартовым экраном `Editor` после login: слева показывает панель `Мои наряды`, справа пустую карту с basemap.
- `src/components/MapView.vue` является основным рабочим экраном карты, выбора слоя, сохранения/удаления и realtime-индикатора. В `mode="empty"` компонент создает только MapLibre basemap без layers/features/realtime/editing overlay.

## State И API

- `src/stores/auth.ts` хранит token/user в `localStorage`, восстанавливает сессию через `/api/v1/auth/me`, очищает состояние при 401.
- `LoginScreen` для HTTP 401 показывает только `message` из structured error
  `{code, message, correlationId}`; legacy `detail` не выводится пользователю,
  если structured `message` отсутствует, используется общий fallback.
- `src/stores/edit.ts` хранит polygon edit session, dirty-state, validation errors и version conflict handling.
- `src/stores/workOrders.ts` хранит назначенные текущему `Editor` work orders, loading/error state и локальный `selectedWorkOrderId`; выбор в списке только подсвечивает строку и не открывает edit version.
- `src/api/http.ts` централизует axios base URL и добавляет Bearer token из Pinia.
- `src/api/layers.ts` оборачивает layer/feature HTTP API и превращает HTTP failures в `HttpError`.
- `src/api/workOrders.ts` вызывает `GET /api/v1/work-orders/assigned-to-me` и использует компактный response contract без audit/internal date fields.

## Карта И Загрузка Данных

MapLibre создается в `src/composables/map/useMapInstance.ts` с центром `[70.1902, 52.937]` и zoom `8`.

`MapPageView` передает `MapView mode="editing"` для существующего editor workspace.
`EditorWorkOrdersView` передает `MapView mode="empty"`, поэтому карта показывает только
подложку и не инициирует загрузку слоев, features, realtime connection или polygon editing.

Основные composables:

- `useLayerSelection` загружает layers, выбирает активный слой и управляет видимостью MapLibre layers.
- `useFeatureLoading` грузит features по видимому bbox, дебаунсит `moveend`, поддерживает client-side tile cache и обновляет GeoJSON source.
- `useFeatureTileCache` хранит features по layer/tile, TTL cache и background pagination при `next_cursor`.
- `useLayerRealtime` подключается к WebSocket слоя, парсит события и переподключается с задержками `500/1000/2000/5000 ms`.
- `usePolygonEditing` синхронизирует overlay редактирования и связывает клики/drag vertices с edit store.

## Редактирование

Текущая интерактивная редактура ориентирована на `Polygon`: выбор feature на карте, перемещение vertex, удаление vertex через context menu, вставка vertex по outline через Shift-click, затем PATCH/DELETE с optimistic `version`.

## Связанные Ноды

- [[api_and_realtime]]
- [[../правила_и_стиль/testing_strategy]]
- [[../dev_setup/local_development]]
