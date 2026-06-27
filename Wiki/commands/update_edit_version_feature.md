---
title: Update Edit Version Feature
type: command
status: planned
created: 2026-06-27
updated: 2026-06-27
source: RAW_inputs/meetings/increment_after_open_workspace.md
tags: [domain-knowledge, command, edit-version, workspace]
confidence: high
related: [Wiki/entities/edit_version, Wiki/specifications/edit_version_has_persisted_change_set, DDD_Wiki/aggregates/edit_version]
---

# Update Edit Version Feature

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

Система сохраняет изменение в `edit_version_features`, выставляет `operation=updated`, возвращает readback текущего состояния feature и делает change set пригодным для draft validation. Это первый обязательный write path после открытия workspace; `submit_for_review` и `ReviewPackage` не должны появляться раньше persisted change set.

## Scope Notes

Первая mutation - update существующего feature: geometry и ограниченный набор editable properties. Create/delete и association mutation откладываются, потому что они требуют дополнительных правил восстановления, referential integrity, network rules и locatability checks.
