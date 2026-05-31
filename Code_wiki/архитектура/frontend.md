---
title: Frontend Architecture
type: service
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [frontend, vue, maplibre, architecture]
---

# Frontend Architecture

Frontend находится в `apps/frontend` и построен на Vue 3, TypeScript, Pinia, Vite и MapLibre GL.

## Входные Точки

- `src/main.ts` подключает MapLibre CSS, общий CSS, Pinia и монтирует `App.vue`.
- `src/App.vue` восстанавливает auth session, показывает `LoginScreen` или авторизованную страницу с `MapPageView`.
- `src/components/MapView.vue` является основным рабочим экраном карты, выбора слоя, сохранения/удаления и realtime-индикатора.

## State И API

- `src/stores/auth.ts` хранит token/user в `localStorage`, восстанавливает сессию через `/api/v1/auth/me`, очищает состояние при 401.
- `src/stores/edit.ts` хранит polygon edit session, dirty-state, validation errors и version conflict handling.
- `src/api/http.ts` централизует axios base URL и добавляет Bearer token из Pinia.
- `src/api/layers.ts` оборачивает layer/feature HTTP API и превращает HTTP failures в `HttpError`.

## Карта И Загрузка Данных

MapLibre создается в `src/composables/map/useMapInstance.ts` с центром `[70.1902, 52.937]` и zoom `8`.

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
