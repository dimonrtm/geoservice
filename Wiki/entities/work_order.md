---
title: Work Order
type: entity
status: active
created: 2026-06-24
updated: 2026-07-25
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; Code_wiki/архитектура/api_and_realtime.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, entity, work-order]
confidence: high
related: [Wiki/actors/editor, Wiki/entities/edit_version, Wiki/value_objects/aoi, DDD_Wiki/aggregates/work_order]
---

# Work Order

## Identity

`WorkOrder` имеет стабильный `id` и человекочитаемый `code`.

## Lifecycle

В Sprint 1 подтвержден минимальный переход `assigned -> in_progress`, который выполняется при первом успешном создании `EditVersion`. First save не создает нового lifecycle transition: `WorkOrder` остается `open/in_progress`.

## Responsibilities

`WorkOrder` связывает назначенного `Editor`, `AOI`, `Feeder`, `DefaultState` и единственную активную `EditVersion`. Для first save он задает внешние ограничения aggregate: editor assignment, AOI, бизнес-контекст, lifecycle и разрешенный scope; атомарное draft state принадлежит `EditVersion`.

## Invariants

- Назначен ровно одному активному `Editor`.
- Открыть задачу может только назначенный `Editor`.
- Ссылается ровно на один `AOI` и один `Feeder`.
- Имеет не более одной активной `EditVersion`.
