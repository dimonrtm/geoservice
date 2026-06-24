---
title: Approve Review Package
type: command
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, command, review, release-2]
confidence: medium
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, Wiki/domain_events/review_package_approved]
---

# Approve Review Package

## Actor

`Reviewer`, а для `Critical` может потребоваться профильный специалист или data owner.

## Target

`ReviewPackage` / `ReviewDecision`.

## Preconditions

- Package содержит обязательные evidence.
- Risk tier согласован.
- Нет hard blockers.
- Approval не stale.

## Outcome

Фиксируется `ReviewDecision`, package получает approval, публикуется [[Wiki/domain_events/review_package_approved]].
