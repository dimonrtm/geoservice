---
title: Update Edit Version Feature Geometry
type: command
status: planned
created: 2026-06-28
updated: 2026-06-29
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md"
tags: [domain-knowledge, command, edit-version, workspace, geometry]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation, Wiki/domain_events/edit_version_change_set_persisted, DDD_Wiki/aggregates/edit_version]
---

# Update Edit Version Feature Geometry

## Actor

`Editor`, назначенный на `WorkOrder`.

## Target

Существующая line `NetworkFeature` внутри open `EditVersion` текущего `WorkOrder` workspace.

## Intent

Сохранить geometry diff существующей линии относительно baseline этой `EditVersion`. Первый deterministic case - сдвиг внутренней вершины линии без изменения endpoints и `NetworkAssociation`; команда не является generic update для любых feature changes.

## Preconditions

- `Editor` назначен на `WorkOrder`.
- `EditVersion` существует, имеет статус `open` и принадлежит этой `WorkOrder`.
- Target feature существует в baseline этой версии и доступен в workspace.
- Изменение касается только геометрии существующей линии.
- Endpoints, association semantics, create/delete и attributes не меняются.
- Resulting geometry валидна и проходит AOI policy.
- `DraftVersionToken` совпадает с текущим draft state; устаревший token означает stale draft и требует refresh.

## Outcome

Система сохраняет geometry diff в persisted draft state, нормализует `operation` как текущее отличие от baseline, возвращает readback persisted feature вместе с explicit baseline diff, вычисляет базовые draft validation flags и фиксирует [[Wiki/domain_events/edit_version_change_set_persisted]], если diff ненулевой. Если геометрия возвращена к baseline, persisted projection должна стать `unchanged`, а не хранить `updated` только из-за прошлого save.

## Out Of Scope

Create/delete feature, изменение attributes, endpoint connectivity, association mutation, topology trace, full topology QA, reconcile, submit for review, `ReviewPackage`, `can_post` и review conflict UI.
