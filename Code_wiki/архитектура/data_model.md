---
title: Data Model And Spatial Storage
type: note
status: active
created: 2026-05-30
updated: 2026-06-15
source: repository-change:2026-06-15
tags: [database, postgis, sqlalchemy, geojson]
---

# Data Model And Spatial Storage

Данные GeoService хранятся в PostgreSQL/PostGIS. Backend использует async SQLAlchemy и GeoAlchemy2.

## Основные Таблицы

- `users`: `id`, `email`, `password_hash`, `role`, `created_at`.
- `layers`: `id`, `name`, `title`, `geometry_type`, `srid`, `storage_table`.
- Feature tables: `feature_points`, `feature_lines`, `feature_polygons`, `feature_multipoints`, `feature_multilines`, `feature_multipolygons`.
- Utility schema `utility_network`: `aois`, `feeders`, `network_features`,
  `network_associations`.

Каждая feature table содержит:

- `id` UUID primary key;
- `geom` PostGIS geometry с SRID 4326 и конкретным geometry type;
- `properties` JSONB;
- `version` integer для optimistic locking;
- `created_at`, `updated_at`.

## Feature Registry

`apps/backend/app/domain/feature_registry.py` связывает `layers.storage_table` с SQLAlchemy model. Это центральное место, которое решает, в какую таблицу читать/писать feature конкретного слоя.

## Spatial Queries

`LayerRepository.list_features_bbox` строит envelope через `ST_MakeEnvelope`, сначала применяет bbox operator `&&`, затем `ST_Intersects`, возвращает geometry как GeoJSON через `ST_AsGeoJSON(...).cast(JSONB)`.

Pagination использует `id > after_id`, сортировку `id ASC`, лимит `limit + 1` и `next_cursor` как id последней возвращенной строки, если результат был truncated.

`UtilityNetworkRepository.get_feeder_aggregate` читает весь feeder одним SQL
statement. Features, associations и AOI формируются независимыми correlated
JSONB subqueries; AOI проверяют наличие пересекающего feature через
`EXISTS`/`ST_Intersects`.

## Миграции И Seed

Alembic migrations лежат в `apps/backend/app/alembic/versions`:

- `431fdb240d56_feature_lines.py` создает `feature_lines`.
- `0d9dcd16a92c_add_all_types_features.py` добавляет остальные feature tables.
- `7f4dbcd151ee_add_layers.py` создает и upsert'ит стартовые слои.
- `c6cef6320f1d_create_users.py` создает users.
- `d3a01f4e9c21_network_model.py` создает utility schema, feeder graph,
  geometry/FK/check constraints и spatial indexes.

После migrations backend запускает module runners demo users и utility
dataset. `synthetic_utility_feeder_01` создаётся атомарно только при отсутствии
feeder с этим code; существующий aggregate не синхронизируется и не
перезаписывается.

## Связанные Ноды

- [[backend]]
- [[api_and_realtime]]
- [[../deployment/docker_compose]]
