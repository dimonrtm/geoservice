---
title: Submit For Review
type: command
status: planned
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, command, review]
confidence: medium
related: [Wiki/entities/edit_version, Wiki/specifications/edit_version_ready_for_review, DDD_Wiki/aggregates/review_package]
---

# Submit For Review

## Actor

`Editor`.

## Target

`EditVersion` и `ReviewPackage`.

## Preconditions

- Edit version прошла validation.
- Reconcile выполнен для текущего `Default` snapshot.
- Не осталось unresolved conflicts, которые блокируют review.
- Собраны минимальные evidence refs/checksums и editor summary.

## Outcome

Создается `ReviewPackage` для `Reviewer`; package переходит в `ready_for_review` / `under_review` path и становится входом для reviewer decision.
