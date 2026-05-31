---
title: Release 1 API Contract Requirements
type: api-endpoint
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [api, release-1, contract, realtime, geojson]
---

# Release 1 API Contract Requirements

Эта нода фиксирует desired contract из `RAW_inputs/documents/спринт 1.odt`. Это требования источника, а не автоматическое утверждение, что текущий код полностью им соответствует.

## Layers Discovery

`GET /api/v1/layers`

- Auth: `Viewer` или `Editor`.
- Response должен возвращать минимум слои `points`, `polygons`, `lines`; источник также допускает multi-geometry layers.
- Каждый Layer содержит `id: UUID`, `name`, `title`, `geometryType`, `srid: 4326`.
- Frontend должен узнавать доступные слои только через этот endpoint, без hardcoded table endpoints.

## Bbox Features

`GET /api/v1/layers/{layerId}/features?bbox=minLon,minLat,maxLon,maxLat&limit=500`

- Response: GeoJSON `FeatureCollection`.
- `bbox` формат: 4 числа WGS84 `minLon,minLat,maxLon,maxLat`.
- Validation: `minLon < maxLon`, `minLat < maxLat`, значения в допустимых диапазонах; иначе `422`.
- Unknown `layerId`: `404`.
- Фильтрация: вернуть только Feature, которые пересекают bbox.
- PostGIS semantics: `ST_MakeEnvelope(minLon, minLat, maxLon, maxLat, 4326)` + `ST_Intersects(geom, envelope)`.
- `limit`: default 500, max 5000.

## Feature Edit

`PATCH /api/v1/layers/{layerId}/features/{featureId}`

- Auth: `Editor`.
- Body: обязательные `version`, `properties`, `geometry`.
- On success: `200` и обновленная GeoJSON Feature с `version = old + 1`.
- On mismatch: `409` и `VERSION_MISMATCH`; изменения не сохраняются.
- Other errors: `403` для `Viewer`, `404` для unknown layer/feature, `422` для invalid geometry/coordinates/payload.

`DELETE /api/v1/layers/{layerId}/features/{featureId}`

- Body содержит обязательный `version`.
- On success: объект удаляется, уходит realtime event.
- On mismatch: `409`, объект не удаляется.
- Missing version: `422` с `VERSION_REQUIRED`.

## Realtime

- Изменения create/update/delete рассылаются подписчикам слоя как `feature_created`, `feature_updated`, `feature_deleted`.
- Цель задержки для других клиентов: 1-2 секунды.
- При reconnect клиент должен переподписаться и выполнить GET bbox для синхронизации.

## GeoJSON Import

`POST /api/v1/layers/{layerId}/imports/geojson`

- Auth: `Editor`.
- SYNC import только для небольших файлов.
- `Content-Length <= 20MB`, иначе `413`.
- Payload должен быть GeoJSON `FeatureCollection`, иначе `422`.
- `Feature.geometry.type` должен совпадать с `Layer.geometryType`, иначе `422`.
- Success response: `{ importId, insertedCount, rejectedCount, errors[] }`, где `errors[]` ограничен 50 элементами.
- После успешного import данные должны быть видны через bbox endpoint.

## Data Format

- GeoJSON.
- SRID: `4326`.
- Координаты: `[lon, lat]`.
- `version` хранится top-level в Feature и должен быть `integer >= 1`.
- Поддерживаемые `geometryType`: `Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, `MultiPolygon`.

## Contract Policy

- Source of truth: этот source document и OpenAPI, когда появится.
- Breaking changes запрещены в рамках Release 1.
- Любое изменение shape API должно идти в одном PR/MR с соответствующим frontend update.

## Связанные Ноды

- [[api_and_realtime]]
- [[data_model]]
- [[../../Vision_wiki/solution/USM]]
- [[../../Vision_wiki/concepts/first_release_mvp]]
