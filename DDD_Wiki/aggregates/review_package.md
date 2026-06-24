---
title: Review Package Aggregate
type: aggregate
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, ddd, aggregate, review]
confidence: medium
related: [Wiki/entities/review_decision, Wiki/value_objects/risk_tier, Wiki/policies/reviewer_post_policy]
---

# Review Package Aggregate

## Aggregate Root

`ReviewPackage` - запланированный aggregate root для consequence-first decision support перед post.

## Consistency Boundary

Package snapshot, evidence, risk tier, blockers, approval и stale status должны быть согласованы для конкретного reconcile/default state.

## Protected Invariants

- `approve package` не равно `can post`.
- Stale approval блокирует post.
- Число false-safe verdict должно оставаться нулевым для hard-block scenarios.
