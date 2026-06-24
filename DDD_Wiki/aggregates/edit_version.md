---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

Sprint 1 трактует workspace как read-only после открытия; последующие спринты добавляют persistence для change set и editing semantics.

## Protected Invariants

- `baseNetworkRevision` неизменяем после создания.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
