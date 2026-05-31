---
title: Release 1 Source Summary
type: session
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [session, release-1, requirements, mvp]
---

# Release 1 Source Summary

## Контекст

`RAW_inputs/documents/спринт 1.odt` описывает 14-дневный план первого релиза для одного разработчика. Цель релиза: MVP совместного редактирования геоданных поверх Vue + MapLibre и FastAPI + PostGIS, с базовой авторизацией, CI/CD, контрактами API, optimistic concurrency и WebSocket-обновлениями.

## Главные Тезисы

- Главная демонстрация Release 1: две вкладки редактируют одну и ту же Feature в одном Layer; первая сохраняет изменение, вторая получает `409 Conflict`, перезагружает актуальную версию и может повторить редактирование.
- Источник фиксирует три основные user stories: просмотр данных на карте, редактирование с optimistic concurrency, небольшой SYNC GeoJSON import до 20MB.
- Минимальный слой API должен включать `GET /api/v1/layers`, bbox-загрузку `GET /api/v1/layers/{layerId}/features?bbox=...&limit=...`, `PATCH`/`DELETE` с обязательным `version`, WebSocket broadcast `feature_created`/`feature_updated`/`feature_deleted`.
- Роли Release 1 ограничены `Viewer` и `Editor`: все запросы требуют Bearer token; `Viewer` читает, `Editor` читает и меняет данные.
- Data format: GeoJSON, SRID 4326, координаты `[lon, lat]`, bbox `minLon,minLat,maxLon,maxLat`, top-level `version`, совпадение `Feature.geometry.type` с `Layer.geometryType`.

## Решения И Требования

- Для конфликтов выбран optimistic concurrency: сервер применяет изменение только если `request.version == stored.version`; иначе возвращает `409` с `VERSION_MISMATCH`.
- `bbox` должен валидироваться как четыре числа в WGS84; backend использует `ST_MakeEnvelope(..., 4326)` и `ST_Intersects`; `limit` по умолчанию 500, максимум 5000.
- SYNC GeoJSON import принимает только `FeatureCollection`, ограничен 20MB, проверяет `geometryType`, возвращает `{ importId, insertedCount, rejectedCount, errors[] }`, где `errors[]` ограничен 50 элементами.
- Non-goals Release 1: CRDT/OT merge, offline mode, locks, multi-object transactions, rich-permissions ACL, полноценная топологическая гео-валидация, большие импорты SHP/GeoPackage.

## Follow-up

- [x] Актуальность `RAW_inputs/documents/спринт 1.odt` подтверждена 2026-05-31: это план первого релиза, а не план спринта.
- [ ] Сверить текущую реализацию с desired contract из [[../../Code_wiki/архитектура/api_contract_first_release_requirements]].

## Links

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../solution/nfr]]
- [[../solution/architecture_vision]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
- [[2026-05-31-initial-discover]]
