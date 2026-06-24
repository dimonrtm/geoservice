---
title: Edit Version Ready For Review
type: specification
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/concepts/utility_gis_editing_domain.md"
tags: [domain-knowledge, specification, review]
confidence: medium
related: [Wiki/entities/edit_version, Wiki/commands/submit_for_review, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Edit Version Ready For Review

## Predicate

Edit version завершила обязательные шаги validation/reconcile и не имеет unresolved conflicts, которые блокируют отправку на review.

## Failure Meaning

Review был бы небезопасным или преждевременным; editor должен устранить blockers, повторить validation/reconcile или предоставить missing evidence.

## Used By

`SubmitForReview` и будущее создание review package.
