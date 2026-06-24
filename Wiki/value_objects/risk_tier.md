---
title: Risk Tier
type: value-object
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, value-object, review, release-2]
confidence: high
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

## Classification Rules

- `Normal`: нет association delta, terminal-sensitive asset, network attribute change, validation clean, dirty areas cleared, trace fixture unchanged или не требуется.
- `High`: есть association delta или terminal-adjacent conflict, но нет подтвержденного изменения trace/subnetwork semantics.
- `Critical`: меняется trace path, затронут subnetwork controller/critical device, меняется traversability через terminal/connectivity, появляется invalid/dirty subnetwork или меняется network attribute, используемый для condition barrier/flow logic.
