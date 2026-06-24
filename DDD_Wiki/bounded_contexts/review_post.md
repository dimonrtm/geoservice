---
title: Review Post Context
type: bounded-context
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md"
tags: [domain-knowledge, ddd, bounded-context, review]
confidence: medium
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, Wiki/policies/stale_approval_policy]
---

# Review Post Context

## Ubiquitous Language Boundary

`ReviewPackage`, `ReviewDecision`, `approve package`, `can post`, `stale approval`, `RiskTier`, `hard blocker` и `PostToDefault` входят в этот контекст.

## Model Ownership

Контекст владеет package review, approval semantics, stale rules и post gate. Он не должен дублировать native conflict editor или topology engine.

## Interfaces

Потребляет evidence из edit version/reconcile в [[DDD_Wiki/bounded_contexts/work_order]] и utility network facts из [[DDD_Wiki/bounded_contexts/utility_network]]; отправляет audit facts в [[DDD_Wiki/bounded_contexts/audit]].
