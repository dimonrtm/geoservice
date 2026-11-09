---
title: Work Order Lifecycle
type: state-machine
status: active
created: 2026-06-24
updated: 2026-11-09
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md"
tags: [domain-knowledge, ddd, state-machine]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, DDD_Wiki/use_cases/utility_editor_workflow, DDD_Wiki/use_cases/withdraw_review_package, DDD_Wiki/use_cases/correct_published_result]
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

## Исключения review/post — 2026-11-09

Линейный путь выше дополнен [[DDD_Wiki/use_cases/withdraw_review_package]]: принятый отзыв завершает возможность post конкретного пакета, но не отменяет сохранённую геометрию, не меняет baseline и не открывает закрытый/отменённый WorkOrder. withdrawn — доменный термин пакета, не новый статус WorkOrder или Save.

[[DDD_Wiki/use_cases/correct_published_result]] сохраняет закрытый исходный цикл. Если нужно исправлять данные, создаётся новый связанный WorkOrder с собственным актуальным baseline и новым review/post. Законные последующие изменения сохраняются; старый snapshot не накатывается. Только evidence исправляется отдельной редакцией и решением применимости без фиктивного Save/post.

Разбор коррекции, исправительный наряд и приёмка получателя завершаются по разным основаниям. [[Wiki/specifications/published_result_correction_closed]] сохраняет открытые остатки и ограничения. Правила приняты условной организацией; runtime не подтверждён.
