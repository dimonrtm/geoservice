---
title: NFR
type: solution
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [solution, nfr, release-1]
---

# NFR

NFR для Release 1 по `RAW_inputs/documents/спринт 1.odt`.

## Performance

- Realtime updates должны доходить до других клиентов через WebSocket в течение 1-2 секунд.
- Bbox loading обязателен для карты; запросы без валидного bbox не должны становиться неограниченной загрузкой данных.
- `limit` для bbox endpoint: default 500, max 5000.
- GeoJSON import в Release 1 только SYNC и только до 20MB.

## Security

- Все API endpoints требуют валидный Bearer token.
- `401 Unauthorized`: token отсутствует или невалиден.
- `403 Forbidden`: `Viewer` пытается выполнить `POST`/`PATCH`/`DELETE`.
- Роли Release 1: `Viewer` только читает, `Editor` читает, создает, редактирует и удаляет.
- CORS должен ограничиваться нужными origins; refresh token отложен.

## Availability

- Источник требует воспроизводимый запуск: DB up -> API up -> Front up -> map shows data.
- CI/CD или локальный pseudo-CI должен иметь зеленые lint/tests/build commands.
- При WebSocket reconnect frontend должен переподписаться и выполнить bbox reload для восстановления консистентности.

## Data And Compliance

- Формат данных: GeoJSON.
- SRID: 4326.
- Порядок координат: `[lon, lat]`.
- `Feature.geometry.type` должен совпадать с `Layer.geometryType`, иначе `422`.
- Координаты должны быть в диапазонах lon `[-180, 180]`, lat `[-90, 90]`, иначе `422`.
- `version` хранится top-level и обязателен для edit/delete concurrency.

## Maintainability

- Контракты backend/frontend нельзя менять breaking changes в течение Release 1.
- Любое изменение API shape должно идти вместе с frontend update в одном PR/MR.
- Все изменения БД идут через миграции, не руками в production.
- Зависимости backend направлены внутрь: `api -> services -> repositories -> db/models`.
- Documentation DoD: run docs, API endpoints, WebSocket protocol, ограничения MVP.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
