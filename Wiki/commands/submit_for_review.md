---
title: Submit For Review
type: command
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md"
tags: [domain-knowledge, command, review]
confidence: medium
related: [Wiki/entities/edit_version, Wiki/specifications/edit_version_ready_for_review, DDD_Wiki/aggregates/review_package]
---

# Submit For Review

## Actor

`Editor`.

## Target

`EditVersion` и будущий `ReviewPackage`.

## Preconditions

- Edit version прошла validation.
- Reconcile выполнен или запланирован по workflow.
- Не осталось unresolved conflicts, которые блокируют review.

## Outcome

Создается review package для `Reviewer`; edit version переходит в состояние, готовое к review, если это подтверждено будущей state machine.
