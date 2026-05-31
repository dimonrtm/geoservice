---
title: Architecture Vision
type: solution
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [solution, architecture, release-1]
---

# Architecture Vision

Высокоуровневое видение Release 1 MVP по `RAW_inputs/documents/спринт 1.odt`. Детальные текущие факты реализации остаются в `Code_wiki/архитектура/`.

## Системы И Границы

| Система | Ответственность | Граница |
|---|---|---|
| Frontend Vue + MapLibre | Login state, layer discovery, bbox loading, edit UI, conflict notification, WebSocket subscription | Не хранит source-of-truth; применяет API/WS contracts и перезагружает данные после reconnect/conflict. |
| Backend FastAPI | REST API, auth, role checks, feature validation, optimistic concurrency, WebSocket broadcast | HTTP/WebSocket boundary под `/api/v1`; бизнес-правила в services, SQL в repositories. |
| Postgres + PostGIS | Хранение geometry/properties/version, spatial filtering, GiST indexes | SRID 4326; bbox через `ST_MakeEnvelope`/`ST_Intersects`. |
| CI/dev environment | Воспроизводимость разработки и demo | Docker Compose, lint/tests/build/smoke commands, README/run docs. |

## Потоки Данных

| Поток | Источник | Получатель | Примечания |
|---|---|---|---|
| Layers discovery | Frontend | `GET /api/v1/layers` | Возвращает UUID layers и geometry metadata; frontend не hardcode'ит table endpoints. |
| Map bbox loading | Map viewport | Backend/PostGIS | `GET /api/v1/layers/{layerId}/features?bbox=...&limit=...`, FeatureCollection response. |
| Feature edit | Editor UI | Backend service/repository | `PATCH` с `version`; success increments version, mismatch returns `409`. |
| Delete | Editor UI | Backend service/repository | `DELETE` требует `version`; mismatch не удаляет объект. |
| Realtime broadcast | Backend after create/update/delete | WebSocket subscribers | События слоя доставляются другим клиентам за 1-2 секунды. |
| GeoJSON import | Editor upload | Backend/PostGIS | SYNC import `FeatureCollection <=20MB`, summary response, данные видны через bbox. |

## Ключевые Компромиссы

| Решение | Альтернатива | Почему |
|---|---|---|
| Optimistic concurrency через `version` и `409` | CRDT/OT или locks | Дешевле и достаточно для 2-недельного MVP; silent overwrite запрещен. |
| WebSocket pub/sub по layer | Полный collaborative state engine | Release 1 нужен broadcast изменений, не сложный merge. |
| Bbox loading вместо тайлов/cache/offline | Tile pipeline или offline cache | Быстрее получить end-to-end map loading и ограничить объем данных через `limit`. |
| Две роли `Viewer`/`Editor` | Rich ACL на уровне объектов/полей | Простая модель прав закрывает Release 1 demo. |
| SYNC GeoJSON import <=20MB | Async import pipeline и большие форматы | Достаточно для demo data; большие форматы отложены. |

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
