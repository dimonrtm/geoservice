---
title: Approve Review Package
type: command
status: planned
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, command, review, release-2]
confidence: medium
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, Wiki/domain_events/review_package_approved]
---

# Approve Review Package

## Actor

`Reviewer`. Для `Critical` в developer demo команда завершается `escalated` как terminal non-goal, без симуляции отдельного Specialist/Data Owner workflow.

## Target

`ReviewPackage` / `ReviewDecision`.

## Preconditions

- Package содержит обязательные evidence.
- Risk tier согласован.
- Нет hard blockers.
- Approval не stale.

## Outcome

Фиксируется `ReviewDecision`, package получает semantic approval, публикуется [[Wiki/domain_events/review_package_approved]]. После этого system `post-gate` может вычислить `can_post`; approval само по себе не разрешает simulated/technical post.
