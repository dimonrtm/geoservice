---
title: Work Order Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/default_state, Wiki/entities/edit_version]
---

# Work Order Aggregate

## Aggregate Root

`WorkOrder` - aggregate root для назначенной задачи, AOI scope, `DefaultState` на уровне `WorkOrder` и открытия active `EditVersion`.

## Consistency Boundary

Открытие edit version должно атомарно создать/получить `EditVersion`, зафиксировать `baseNetworkRevision` и перевести `WorkOrder` в `in_progress`, когда это требуется.

## Protected Invariants

- Одно active editor assignment.
- Один `AOI` и один `Feeder` на `WorkOrder`.
- Не больше одной open edit version на `WorkOrder`.
- `Reviewer` не может открыть editor workspace.
