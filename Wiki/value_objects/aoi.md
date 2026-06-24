---
title: AOI
type: value-object
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, value-object, spatial]
confidence: high
related: [Wiki/entities/work_order, DDD_Wiki/bounded_contexts/work_order]
---

# AOI

`AOI` (`Area of Interest`) - именованная географическая область задачи и серверная граница доступного набора данных.

## Equality

Равенство определяется стабильным `id` в persistence и геометрической областью в пределах scope конкретной `WorkOrder`.

## Immutability

Для Sprint 1 `AOI` фиксируется при назначении `WorkOrder`; изменение AOI, несколько AOI на задачу, buffer zones и spatial ACL не входят в scope.

## Used By

`WorkOrder`, workspace filtering и `WorkOrderRepository.get_workspace_aggregate`.
