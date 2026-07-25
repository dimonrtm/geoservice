---
title: AOI
type: value-object
status: active
created: 2026-06-24
updated: 2026-07-25
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, value-object, spatial]
confidence: high
related: [Wiki/entities/work_order, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/bounded_contexts/work_order]
---

# AOI

`AOI` (`Area of Interest`) - именованная географическая область задачи и серверная граница доступного набора данных.

## Equality

Равенство определяется стабильным `id` в persistence и геометрической областью в пределах scope конкретной `WorkOrder`.

## Immutability

Для Sprint 1 `AOI` фиксируется при назначении `WorkOrder`; изменение AOI, несколько AOI на задачу, buffer zones и spatial ACL не входят в scope.

## Visibility And Edit Eligibility

Workspace может показывать features, пересекающие AOI. First-save edit eligibility строже: line feature должна целиком быть `covered by` AOI. Boundary включена, поэтому касание границы разрешено; простого пересечения недостаточно.

## Used By

`WorkOrder`, workspace filtering, `WorkOrderRepository.get_workspace_aggregate` и blocking spatial invariant `UpdateEditVersionFeatureGeometry`.
