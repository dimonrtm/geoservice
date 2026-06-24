---
title: Work Order
type: entity
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; Code_wiki/архитектура/api_and_realtime.md"
tags: [domain-knowledge, entity, work-order]
confidence: high
related: [Wiki/actors/editor, Wiki/entities/edit_version, Wiki/value_objects/aoi, DDD_Wiki/aggregates/work_order]
---

# Work Order

## Identity

`WorkOrder` имеет стабильный `id` и человекочитаемый `code`.

## Lifecycle

В Sprint 1 подтвержден минимальный переход `assigned -> in_progress`, который выполняется при первом успешном создании `EditVersion`.

## Responsibilities

`WorkOrder` связывает назначенного `Editor`, `AOI`, `Feeder`, `DefaultState` и единственную активную `EditVersion`.

## Invariants

- Назначен ровно одному активному `Editor`.
- Открыть задачу может только назначенный `Editor`.
- Ссылается ровно на один `AOI` и один `Feeder`.
- Имеет не более одной активной `EditVersion`.
