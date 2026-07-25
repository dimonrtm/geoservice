---
title: Stale Approval Policy
type: policy
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, policy, stale-approval]
confidence: high
related: [Wiki/entities/default_state, Wiki/entities/review_decision, Wiki/specifications/post_allowed]
---

# Stale Approval Policy

## Rule

Approval становится stale, если после package build/approval изменился один из факторов, на которых основано решение: `Default`, geometry, association delta, network attribute, terminal configuration, validation result, trace/subnetwork freshness, required evidence или rule/configuration state, требующий нового reconcile.

## Inputs

`DefaultState.baseNetworkRevision`, package snapshot/version ids, reconcile run, validation result, freshness trace/subnetwork, association delta, network attributes, terminal configuration и timestamps evidence.

## Decision Outcome

Stale package блокирует `PostToDefault` и требует repeat review или recompute package.

## Mandatory Stale Events

- Новый reconcile.
- `DefaultChangedAfterReconcile` как главный negative fixture.
- Изменение `Default` в package scope.
- Изменение geometry, association delta, network attribute или terminal configuration.
- Изменение validation result, trace/subnetwork freshness или required evidence после approval.
