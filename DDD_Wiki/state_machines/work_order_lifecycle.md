---
title: Work Order Lifecycle
type: state-machine
status: active
created: 2026-06-24
updated: 2026-06-26
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, ddd, state-machine]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Work Order Lifecycle

## Sprint 1 States

```text
Assigned -> InProgress
```

## Canonical Review/Post Direction

Минимальный линейный путь после `InProgress`:

```text
editing -> validated -> reconciled -> draft_package -> ready_for_review -> under_review -> approved | returned | escalated -> can_post | blocked_post | stale -> simulated_posted
```

`can_post` не является durable state; это computed specification на чтении. Durable audit хранит snapshot pre-post check, post attempt и simulated/final outcome. `approve package` и `can_post` разделены намеренно: reviewer decision не равен техническому допуску к `PostToDefault`.
