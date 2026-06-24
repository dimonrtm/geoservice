---
title: Work Order Context
type: bounded-context
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, ddd, bounded-context]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, Wiki/value_objects/aoi, DDD_Wiki/aggregates/work_order]
---

# Work Order Context

## Ubiquitous Language Boundary

Внутри контекста термины `WorkOrder`, `AOI`, `DefaultState`, `EditVersion`, `assigned`, `in_progress`, `workspace` имеют точный смысл. `AOI` принадлежит scope `WorkOrder`, а не `utility_network`.

## Model Ownership

Контекст владеет `WorkOrder`, `AOI`, lifecycle `EditVersion` для открытия workspace и `DefaultState` на уровне `WorkOrder`.

## Interfaces

Потребляет current utility network snapshot из [[DDD_Wiki/bounded_contexts/utility_network]] и предоставляет workspace editor UI/API.
