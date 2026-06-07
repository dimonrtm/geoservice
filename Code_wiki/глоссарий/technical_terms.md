---
title: Technical Terms
type: glossary
status: active
created: 2026-05-30
updated: 2026-06-07
source: "repository-snapshot:2026-05-30; RAW_inputs/documents/utility_gis_editor_domain_dictionary.md"
tags: [glossary, geoservice, utility-network]
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

## Desired Utility Demo Vocabulary

Эти термины описывают desired domain model из RAW source и Ф4 walking skeleton. Они не означают, что соответствующий API или production-grade механизм уже реализован.

- `WorkOrder` - контекст задачи на изменение инженерной сети и связанного `AOI`.
- `NetworkFeature` - общий пространственный объект сети: line, device, junction или assembly.
- `NetworkAssociation` - непространственная связь между сетевыми объектами.
- `NetworkVersion` / `Edit version` - рабочий изолированный контекст изменений относительно `Default`.
- `ChangeSet` - набор edits, сохраняемый отдельно от authoritative state до post.
- `ValidationIssue` - результат проверки demo network rules, topology или connectivity.
- `Reconcile` - сравнение рабочей версии с актуальным `Default`.
- `Conflict` - несовместимое изменение attribute, geometry, object lifecycle или association.
- `ConflictResolution` - явный выбор `Mine`, `Default` или manual merge перед publication.
- `PostToDefault` - публикация проверенных изменений в authoritative state; не синоним обычного save.
- `AuditLog` - цепочка actor/action/time/work order/version/before-after/review/result.

Domain commands `CreateEditVersion`, `ValidateTopology`, `RunReconcile`, `ResolveConflict` и `PostToDefault` пока являются словарем проектирования, а не утвержденными endpoint names.

## Связанные Ноды

- [[../архитектура/backend]]
- [[../архитектура/frontend]]
- [[../архитектура/data_model]]
- [[../../Vision_wiki/concepts/utility_gis_editing_domain]]
- [[../../Vision_wiki/solution/architecture_vision]]
