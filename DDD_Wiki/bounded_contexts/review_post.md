---
title: Review Post Context
type: bounded-context
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, ddd, bounded-context, review]
confidence: high
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, Wiki/policies/stale_approval_policy]
---

# Review Post Context

## Ubiquitous Language Boundary

`ReviewPackage`, `ReviewDecision`, `approve package`, `can post`, `stale approval`, `RiskTier`, `hard blocker` и `PostToDefault` входят в этот контекст.

## Model Ownership

Контекст владеет package review, approval semantics, stale rules и post gate. Он не должен дублировать native conflict editor или topology engine. Семантическое approval принадлежит `Reviewer`; технический `PostToDefault` принадлежит `Publisher` / version administrator или demo-system action в ближайшем срезе.

## Interfaces

Потребляет evidence из edit version/reconcile в [[DDD_Wiki/bounded_contexts/work_order]] и utility network facts из [[DDD_Wiki/bounded_contexts/utility_network]]; отправляет audit facts в [[DDD_Wiki/bounded_contexts/audit]].

## Nearest Vertical Slice

Ближайший 14-дневный срез должен проверить путь `work order -> named edit version -> validation -> reconcile -> package build -> reviewer decision -> stale/blocker recheck -> simulated post -> audit outcome`.
