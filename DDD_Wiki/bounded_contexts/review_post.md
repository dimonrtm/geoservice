---
title: Review Post Context
type: bounded-context
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, ddd, bounded-context, review]
confidence: high
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, Wiki/policies/stale_approval_policy]
---

# Review Post Context

## Ubiquitous Language Boundary

`ReviewPackage`, `ReviewDecision`, `approve package`, `can_post`, `stale approval`, `RiskTier`, `absolute veto`, `pre-post check`, `simulated post` и `PostToDefault` входят в этот контекст.

## Model Ownership

Контекст владеет package review, approval semantics, stale rules, computed `can_post`, simulated post и post gate. Он не должен дублировать native conflict editor или topology engine. Семантическое approval принадлежит `Reviewer`; technical post в developer demo выполняет system actor `post-gate`, а целевая future-модель сохраняет отдельную роль `Publisher` / version administrator для authoritative `PostToDefault`.

## Interfaces

Потребляет evidence из edit version/reconcile в [[DDD_Wiki/bounded_contexts/work_order]] и utility network facts из [[DDD_Wiki/bounded_contexts/utility_network]]; отправляет audit facts в [[DDD_Wiki/bounded_contexts/audit]].

## Nearest Vertical Slice

Ближайший путь должен идти маленькими спринтами через существующий flow: `WorkOrder` -> `EditVersion` -> validation/reconcile -> `submit_for_review` -> package build -> reviewer decision -> computed `can_post` -> simulated post -> durable audit. Legacy standalone Release 2 contract не является source of truth для этого slice.
