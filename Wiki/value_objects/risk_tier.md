---
title: Risk Tier
type: value-object
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, value-object, review, release-2]
confidence: medium
related: [Wiki/entities/review_decision, Wiki/policies/reviewer_post_policy, DDD_Wiki/aggregates/review_package]
---

# Risk Tier

`RiskTier` классифицирует сетевой риск package: `Normal`, `High`, `Critical`.

## Equality

Равенство определяется значением tier и набором фактов, которые обосновали его в package evidence.

## Immutability

Risk tier должен фиксироваться в audit для конкретной версии package. Изменение evidence или `Default` создает новый или stale package, а не незаметно переписывает прежний tier.

## Used By

`ReviewerPostPolicy`, routing/escalation и consequence package для Release 2.
