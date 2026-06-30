---
title: Update Edit Version Feature Geometry
type: command
status: planned
created: 2026-06-28
updated: 2026-06-30
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
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

Сохранить geometry-only изменение существующей линии относительно baseline этой `EditVersion`. Первый deterministic case - сдвиг одной или нескольких внутренних вершин линии без изменения start/end vertices, `part count`, vertex identity и `NetworkAssociation`; команда не является generic update для любых feature changes.

## Preconditions

- `Editor` назначен на `WorkOrder`.
- `EditVersion` существует, имеет статус `open` и принадлежит этой `WorkOrder`.
- Target feature существует в baseline этой версии и доступен в workspace.
- Изменение касается только геометрии существующей линии.
- Start/end vertices, association semantics, create/delete, split/merge, attributes, `part count` и vertex count не меняются.
- Resulting geometry валидна и целиком остается внутри AOI.
- `DraftVersionToken` совпадает с текущей версией агрегата `EditVersion`; устаревший token означает stale draft и требует refresh.

## Outcome

Система сохраняет full resulting geometry snapshot как persisted draft state и вычисляет diff относительно baseline как производный артефакт. Readback возвращает resulting feature, новый `DraftVersionToken`, `operation` / `hasPersistedChangeSet` и validation summary; explicit diff можно вычислять или возвращать позже для review/readback удобства, но это не minimum proof первого save. Если геометрия возвращена к baseline, persisted projection должна стать `unchanged`, `hasPersistedChangeSet=false`, `dirtyRelativeToBaseline=false`, а не хранить `updated` только из-за прошлого save.

[[Wiki/domain_events/edit_version_change_set_persisted]] фиксируется при переходе `unchanged -> updated`, когда впервые появляется ненулевой persisted change set. Повторный identical retry не создает новое событие; для retry UX нужен отдельный `CommandId` / idempotency key.

## Out Of Scope

Create/delete feature, изменение attributes, endpoint connectivity, vertex insert/delete, split/merge, association mutation, topology trace, full topology QA, live-`Default` freshness check, reconcile, submit for review, `ReviewPackage`, `can_post` и review conflict UI.
