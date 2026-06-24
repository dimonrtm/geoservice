---
title: Edit Version Ready For Review
type: specification
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/concepts/utility_gis_editing_domain.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, specification, review]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/submit_for_review, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Edit Version Ready For Review

## Predicate

Edit version готова к review, если выполнен последний reconcile с текущим `Default`, нет unreviewed/unresolved conflicts, validation не содержит absolute veto errors, собран минимальный evidence package, заполнен editor summary/comment и package имеет зафиксированный built-from state.

## Failure Meaning

Review был бы небезопасным или преждевременным; edit version должна перейти в `blocked`, а editor должен устранить blockers, повторить validation/reconcile или предоставить missing evidence.

## Used By

`SubmitForReview` и будущее создание review package.
