---
title: Work Order Lifecycle
type: state-machine
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md"
tags: [domain-knowledge, ddd, state-machine]
confidence: medium
related: [Wiki/entities/work_order, Wiki/entities/edit_version, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Work Order Lifecycle

## Sprint 1 States

```text
Assigned -> InProgress
```

## Full Release Direction

Release roadmap расширяет путь через editing, validation, reconcile, conflict resolution, review, post и audit. Точные имена состояний после `InProgress` остаются planned.

## Open Questions

Состояния review/post нужно согласовать с package state machine из Release 2, прежде чем считать их каноническими.
