---
title: Edit Version Ready For Review
type: specification
status: active
created: 2026-06-24
updated: 2026-06-28
source: "docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/concepts/utility_gis_editing_domain.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, specification, review]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/submit_for_review, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Edit Version Ready For Review

## Predicate

Edit version готова к review только после появления persisted change set. Минимальный predicate начинается с [[Wiki/specifications/edit_version_has_persisted_change_set]], затем требует [[Wiki/specifications/edit_version_basic_draft_validation]] без базовых blockers, editor summary/evidence и freshness check перед submit. Полный review/post predicate дополнительно требует последний reconcile с текущим `Default`, отсутствие unreviewed/unresolved conflicts, отсутствие absolute veto errors и зафиксированный built-from state для будущего `ReviewPackage`.

## Failure Meaning

Review был бы небезопасным или преждевременным. Если persisted change set отсутствует, это не blocker review, а еще не достигнутый предыдущий слой workflow; сначала нужен edit-save-readback. Если change set есть, editor должен устранить blockers, повторить validation/reconcile или предоставить missing evidence.

## Used By

`SubmitForReview` и будущее создание review package.
