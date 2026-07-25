---
title: Edit Version
type: entity
status: active
created: 2026-06-24
updated: 2026-07-25
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; Code_wiki/архитектура/api_and_realtime.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, entity, edit-version]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/default_state, Wiki/commands/open_edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/draft_version_token, Wiki/value_objects/command_id, DDD_Wiki/aggregates/edit_version]
---

# Edit Version

## Identity

`EditVersion` имеет стабильный `id`, `workOrderId`, `ownerId` и `baseNetworkRevision`.

## Lifecycle

Состояние в Sprint 1: `open`. Повторное открытие возвращает уже открытую active version и обновляет `lastOpenedAt`. First save не меняет lifecycle: `EditVersion` остается `open`, а `WorkOrder` - `open/in_progress`.

## Responsibilities

Изолирует рабочий контекст одной `WorkOrder` от authoritative `Default`. Создается как deep copy активного `DefaultState`. Для first save агрегат хранит immutable baseline snapshot и full current snapshot одной изменяемой line `NetworkFeature`; current diff, `operation` и `hasPersistedChangeSet` вычисляются относительно baseline. Persisted draft сопровождается `DraftVersionToken` и `basicValidation`.

## Invariants

- Принадлежит одному `WorkOrder` и назначенному `Editor`.
- `baseNetworkRevision` фиксируется при создании и не меняется.
- У одной `WorkOrder` не больше одной open edit version.
- Непустой first-slice change set меняет geometry только одной существующей линии во всей версии и допускает сдвиг ровно одной внутренней вершины; equality с baseline допустима для revert/no-op. Endpoints, остальные вершины, associations, attributes, create/delete и structure changes остаются вне scope.
- Baseline snapshot внутри `EditVersion` неизменяем и не подменяется live-состоянием `Default` на save.
- `operation` отражает текущий persisted diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` защищает save от stale draft.
- `CommandId` обеспечивает idempotent retry и не подменяет `DraftVersionToken`.
- `ReviewPackage` не создается до появления persisted change set; до submit summary/evidence могут храниться рядом с `EditVersion` как draft.
