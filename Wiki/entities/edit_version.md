---
title: Edit Version
type: entity
status: active
created: 2026-06-24
updated: 2026-06-28
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; Code_wiki/архитектура/api_and_realtime.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, entity, edit-version]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/default_state, Wiki/commands/open_edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/draft_version_token, DDD_Wiki/aggregates/edit_version]
---

# Edit Version

## Identity

`EditVersion` имеет стабильный `id`, `workOrderId`, `ownerId` и `baseNetworkRevision`.

## Lifecycle

Состояние в Sprint 1: `open`. Повторное открытие возвращает уже открытую active version и обновляет `lastOpenedAt`.

## Responsibilities

Изолирует рабочий контекст одной `WorkOrder` от authoritative `Default`. Создается как deep copy активного `DefaultState`. Следующий planned responsibility - хранить persisted change set workspace edits: сначала geometry diff существующей line `NetworkFeature`, затем readback diff и basic draft validation flags.

## Invariants

- Принадлежит одному `WorkOrder` и назначенному `Editor`.
- `baseNetworkRevision` фиксируется при создании и не меняется.
- У одной `WorkOrder` не больше одной open edit version.
- First save меняет только geometry существующей линии; endpoints, associations, attributes и create/delete остаются вне scope.
- `operation` отражает текущий persisted diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` защищает save от stale draft.
- `ReviewPackage` не создается до появления persisted change set; до submit summary/evidence могут храниться рядом с `EditVersion` как draft.
