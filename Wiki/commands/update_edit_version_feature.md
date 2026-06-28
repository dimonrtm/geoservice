---
title: Update Edit Version Feature
type: command
status: superseded
created: 2026-06-27
updated: 2026-06-28
source: "RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, command, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature_geometry, Wiki/entities/edit_version, Wiki/specifications/edit_version_has_persisted_change_set, DDD_Wiki/aggregates/edit_version]
---

# Update Edit Version Feature

## Status

Superseded by [[Wiki/commands/update_edit_version_feature_geometry]] for the first persisted edit slice. The generic command name remains a possible future umbrella only after geometry and attributes are intentionally supported together.

## Actor

`Editor`, назначенный на `WorkOrder`.

## Target

Существующий `NetworkFeature` внутри open `EditVersion` текущего `WorkOrder` workspace.

## Preconditions

- `Editor` назначен на `WorkOrder`.
- `EditVersion` существует, имеет статус `open` и принадлежит этому `WorkOrder`.
- Feature входит в `WorkOrder.scope.aoi` и доступен в workspace.
- Изменение относится к разрешенному набору editable geometry/properties.
- Optimistic concurrency не обнаружила более новую версию изменяемой строки.

## Outcome

Старое broad-намерение уточнено: первый write path должен сохранять именно geometry diff существующей линии внутри `EditVersion`, а не произвольный CRUD update feature.

## Scope Notes

Для ближайшего инкремента generic `UpdateEditVersionFeature` слишком широк: attributes, create/delete, association mutation и endpoint rewiring остаются вне scope.
