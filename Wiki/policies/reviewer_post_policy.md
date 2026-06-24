---
title: Reviewer Post Policy
type: policy
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, policy, review]
confidence: medium
related: [Wiki/actors/reviewer, Wiki/value_objects/risk_tier, Wiki/specifications/post_allowed]
---

# Reviewer Post Policy

## Rule

`Reviewer` approves package content, а не один отдельный conflict item. `approve package` и техническое `can post` - разные решения. `High/Critical` нельзя автоматически approve или downgrade.

## Inputs

Risk tier, полнота evidence, validation/topology status, trace/subnetwork impact, work order/evidence, stale status и hard blockers.

## Decision Outcome

Package может быть approved, rejected, escalated, marked stale или blocked from post.

## Exceptions

Для `Normal` без network impact допустим audit + sample review; для `Critical` нужен dual control.
