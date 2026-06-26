---
title: Post Allowed
type: specification
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, specification, post]
confidence: high
related: [Wiki/commands/post_to_default, Wiki/policies/stale_approval_policy, Wiki/policies/reviewer_post_policy]
---

# Post Allowed

## Predicate

`can_post` является computed specification на чтении, а не persisted authoritative state. Predicate true только если package approved, не stale, absolute veto отсутствуют, текущий `Default` все еще соответствует reconcile/post assumptions, required evidence выполняет требования risk tier, а pre-post gate подтверждает freshness, blockers и право simulated/technical post.

## Failure Meaning

Simulated/technical post должен быть заблокирован, чтобы избежать небезопасного или устаревшего authoritative state. Snapshot pre-post check и post outcome сохраняются в audit, но сам `can_post` не сохраняется как вечный флаг.

## Used By

`PostToDefault`, защита stale approval, pre-post gate и simulated post в integrated review/post slice.

## Absolute Veto Set V0.1

- Unresolved association delta.
- Dirty/error state в affected extent или trace path.
- `DefaultChangedAfterReconcile`.
- Changed validation result.
- Invalid subnetwork status для subnetwork-relevant scenario.
- Unexpected trace delta относительно package snapshot.
- Missing evidence только там, где policy делает evidence обязательным для текущего risk tier.
