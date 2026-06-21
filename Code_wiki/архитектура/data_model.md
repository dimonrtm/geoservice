---
title: Data Model And Spatial Storage
type: note
status: active
created: 2026-05-30
updated: 2026-06-21
source: repository-change:2026-06-21
tags: [database, postgis, sqlalchemy, geojson]
---

# Data Model And Spatial Storage

Данные GeoService хранятся в PostgreSQL/PostGIS. Backend использует async SQLAlchemy и GeoAlchemy2.

## Основные Таблицы

- `user.users`: `id`, `email`, `password_hash`, `role`, `created_at`.
- `layers`: `id`, `name`, `title`, `geometry_type`, `srid`, `storage_table`.
- Feature tables: `feature_points`, `feature_lines`, `feature_polygons`, `feature_multipoints`, `feature_multilines`, `feature_multipolygons`.
- Utility schema `utility_network`: `feeders`, `network_features`,
  `network_associations`, `network_states`, per-WorkOrder `default_states`,
  `default_state_features`, `default_state_associations`.
- Work-order schema `work_order`: `aois`, `work_orders`, `edit_versions`,
  `edit_version_features`, `edit_version_associations`.

`utility_network` хранит актуальную инженерную сеть и baseline-срезы для
конкретных work orders, но не владеет AOI. `work_order` хранит агрегат задачи,
`scope.aoi` и рабочую копию baseline. Cross-schema связи между будущими сервисными границами не
закрепляются внешними ключами: идентификаторы пользователя, work order и
сетевого baseline связываются через repositories/application layer. Внутри одной
схемы FK остаются допустимы для внутренних таблиц агрегата или baseline-среза.
`work_order.work_orders.aoi_id` имеет FK только на `work_order.aois.id`.

Каждая feature table содержит:

- `id` UUID primary key;
- `geom` PostGIS geometry с SRID 4326 и конкретным geometry type;
- `properties` JSONB;
- `version` integer для optimistic locking;
- `created_at`, `updated_at`.

## Feature Registry

`apps/backend/utility_service/domain_services/feature_registry.py` связывает
`layers.storage_table` с SQLAlchemy model. Это центральное место, которое
решает, в какую таблицу читать/писать feature конкретного слоя.

## Spatial Queries

`LayerRepository.list_features_bbox` строит envelope через `ST_MakeEnvelope`, сначала применяет bbox operator `&&`, затем `ST_Intersects`, возвращает geometry как GeoJSON через `ST_AsGeoJSON(...).cast(JSONB)`.

Pagination использует `id > after_id`, сортировку `id ASC`, лимит `limit + 1` и `next_cursor` как id последней возвращенной строки, если результат был truncated.

`UtilityNetworkRepository.get_feeder_aggregate` читает feeder одним SQL statement
и возвращает его features/associations без AOI: рабочая область больше не часть
`utility_network`.

`WorkOrderRepository.get_workspace_aggregate` читает workspace для пары
`work_order_id`/`edit_version_id`: `WorkOrder`, `EditVersion`, `work_order.AOI`,
features из `edit_version_features`, пересекающие AOI через `ST_Intersects`, и
associations, у которых оба endpoint feature попали в рабочую область. Geometry
возвращается как GeoJSON через `ST_AsGeoJSON(...).cast(JSONB)`, AOI дополнительно
возвращает extent.

## Миграции И Seed

Alembic migrations лежат в
`apps/backend/utility_service/infrastructure/postgresql/alembic/versions`:

- `431fdb240d56_feature_lines.py` создает `feature_lines`.
- `0d9dcd16a92c_add_all_types_features.py` добавляет остальные feature tables.
- `7f4dbcd151ee_add_layers.py` создает и upsert'ит стартовые слои.
- `c6cef6320f1d_create_users.py` создает схему `user` и таблицу
  `user.users`.
- `d3a01f4e9c21_network_model.py` создает utility schema, feeder graph,
  geometry/FK/check constraints и spatial indexes.
- `e4b7a9c2d5f8_work_orders.py` добавляет
  `work_order.work_orders` со статусами `assigned`/`in_progress`, уникальным
  `code`, индексами для assignment/status lookups и plain UUID полями
  `assignee_user_id`/`created_by_user_id` без FK на `user.users`.
- `a8c1f2d3e4b5_edit_versions.py` добавляет
  `utility_network.network_states`, per-WorkOrder
  `utility_network.default_states`, `default_state_features`,
  `default_state_associations`, а также `work_order.edit_versions`,
  `edit_version_features` и `edit_version_associations`. `DefaultState`
  ссылается на work order plain UUID, хранит `base_network_revision` текущей
  сети и в первом шаге имеет только статус `active`. `EditVersion` хранит
  `base_network_revision`, статус `open` и partial unique index
  `uq_edit_versions_open_work_order` для запрета двух открытых версий одного
  work order.
- `f2b3c4d5e6a7_sprint1_schema_boundaries.py` является schema-boundary миграцией:
  создает схемы `user`/`work_order`, переносит
  `public.users` в `user.users` при необходимости, удаляет legacy
  `utility_network.work_orders`/`utility_network.edit_versions`/`utility_network.aois`,
  создает `work_order.aois`, `work_order.work_orders` с обязательным `aoi_id`
  и новую схему таблиц без compatibility views.
- `c9d0e1f2a3b4_repair_work_order_aoi_scope.py` является repair-миграцией для
  dev/CI volumes, где `alembic_version` уже помечен как `f2b3c4d5e6a7`, но
  физическая таблица `work_order.work_orders` осталась без `aoi_id`. Миграция
  создает `work_order.aois` при необходимости, переносит строки из legacy
  `utility_network.aois`, добавляет `work_orders.aoi_id`, backfill'ит
  отсутствующий scope fallback AOI, восстанавливает `fk_work_orders_aoi` и
  `ix_work_orders_aoi_id`, затем удаляет legacy `utility_network.aois`.

`DefaultState.base_network_revision` должен совпадать с актуальной версией
сети, от которой сделан срез. При `post` несовпадение этой версии с текущей
актуальной сетью должно блокировать публикацию; автоматический refresh
`DefaultState` в Спринте 1 не включен. `EditVersion` создается только при начале
работы как deep copy активного `DefaultState`: feature/association UUID сразу
остаются будущими боевыми UUID для `DefaultState`, меняются сами features,
operation state и версии.

После migrations backend запускает module runners demo users и utility
dataset. `synthetic_utility_feeder_01` создаётся атомарно только при отсутствии
feeder с этим code; существующий aggregate не синхронизируется и не
перезаписывается. Utility dataset seed больше не создаёт AOI.

`seed_work_order_specs.py` и `SeedWorkOrderService` задают create-once seed
`WO-001`: задача назначается `alexey.editor@example.local`, а feeder
`synthetic_utility_feeder_01` используется только как источник сетевого среза
для `DefaultState`. Assignee читается через `SeedUserRepository`, feeder
dependencies читаются через `SeedUtilityDatasetRepository`, а
`SeedWorkOrderRepository` отвечает за work-order-specific операции, создание
`work_order.AOI` scope и per-WorkOrder `DefaultState`. Если `WO-001` уже существует, seed не меняет
assignee, status, title или description, но гарантирует наличие `work_order.AOI`
и активного `DefaultState` для этого work order.

## Связанные Ноды

- [[backend]]
- [[api_and_realtime]]
- [[../deployment/docker_compose]]
