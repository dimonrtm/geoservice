---
title: Work Order Lifecycle
type: state-machine
status: active
created: 2026-06-24
updated: 2026-07-25
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
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

Минимальный линейный путь после `InProgress`, с учетом текущего кода:

```text
workspace_loaded -> persisted_draft_ready -> submit_for_review -> draft_package -> ready_for_review -> under_review -> approved | returned | escalated -> can_post | blocked_post | stale -> simulated_posted
```

`persisted_draft_ready` и `can_post` не являются durable lifecycle states; это computed stages. После first save `EditVersion` остается `open`, `WorkOrder` - `open/in_progress`, а `topologyChecked` - `not_checked`. Durable audit хранит snapshot pre-post check, post attempt и simulated/final outcome. `approve package` и `can_post` разделены намеренно: reviewer decision не равен техническому допуску к `PostToDefault`.

Новые durable review states не добавляются до появления реального submit/reviewer backend. До этого readiness выражается computed predicates поверх persisted geometry change set, basic draft validation, stale marker и editor summary/evidence.
