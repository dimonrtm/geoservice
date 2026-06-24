---
title: Stale Approval Policy
type: policy
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, policy, stale]
confidence: medium
related: [Wiki/entities/default_state, Wiki/entities/review_decision, Wiki/specifications/post_allowed]
---

# Stale Approval Policy

## Rule

Approval становится stale, если после reconcile/approval изменились `Default`, topology-relevant package parts, validation result, association delta, trace path, subnetwork status, blockers или risk-relevant evidence.

## Inputs

`DefaultState.baseNetworkRevision`, package snapshot/version ids, validation result, freshness trace/subnetwork, association delta и timestamps evidence.

## Decision Outcome

Stale package блокирует `PostToDefault` и требует repeat review или recompute package.

## Exceptions

Не зафиксированы; первый implementation contract должен уточнить точные stale events.
