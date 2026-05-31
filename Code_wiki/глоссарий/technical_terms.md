---
title: Technical Terms
type: glossary
status: active
created: 2026-05-30
updated: 2026-05-30
source: repository-snapshot:2026-05-30
tags: [glossary, geoservice]
---

# Technical Terms

- `Layer` - запись в `layers`, описывает имя, title, geometry type, SRID и storage table для набора features.
- `Feature` - GeoJSON feature с `id`, `version`, `properties` и `geometry`.
- `storage_table` - поле layer, по которому backend выбирает SQLAlchemy model через `feature_registry`.
- `version` - integer для optimistic locking при PATCH/DELETE.
- `bbox` - строка `min_lon,min_lat,max_lon,max_lat`, по которой backend строит `ST_MakeEnvelope`.
- `next_cursor` - cursor pagination по `id ASC`, используется при truncated feature collections.
- `FeatureTileCache` - frontend cache, который хранит features по layer и tile key.
- `realtime` - WebSocket подписка `/api/v1/ws/layers/{layer_id}` для событий feature create/update/delete.
- `edit overlay` - MapLibre sources/layers `edit:polygon` и `edit:vertices`, которые показывают draft polygon и vertices.
- `repository-snapshot` - wiki ingest режима текущего состояния репозитория, не основанный на `git diff`.

## Связанные Ноды

- [[../архитектура/backend]]
- [[../архитектура/frontend]]
- [[../архитектура/data_model]]
