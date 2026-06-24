---
title: Reviewer Post Policy
type: policy
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, policy, review]
confidence: high
related: [Wiki/actors/reviewer, Wiki/value_objects/risk_tier, Wiki/specifications/post_allowed]
---

# Reviewer Post Policy

## Rule

`Reviewer` approves package content, а не один отдельный conflict item. `approve package` и техническое `can post` - разные решения. `PostToDefault` принадлежит `Publisher` / version administrator или demo-system action в ближайшем срезе, а не `Reviewer` как владельцу authoritative state.

## Inputs

Risk tier, полнота evidence, validation/topology status, trace/subnetwork impact, work order/evidence, stale status и hard blockers.

## Decision Outcome

Package может быть approved, rejected, escalated, marked stale или blocked from post.

## Risk Authority Matrix

- `Normal`: обязательного второго контроля нет.
- `High`: `Reviewer` принимает основное содержательное решение, если evidence полный.
- `Critical`: требуется подтверждение профильного специалиста; utility-network admin подключается только для rule/configuration/topology governance, а `Data Owner` - для policy override.
