---
title: Post Allowed
type: specification
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, specification, post]
confidence: high
related: [Wiki/commands/post_to_default, Wiki/policies/stale_approval_policy, Wiki/policies/reviewer_post_policy]
---

# Post Allowed

## Predicate

Package approved, не stale, hard blockers отсутствуют, текущий `Default` все еще соответствует reconcile/post assumptions, evidence выполняет требования risk tier, а technical post gate подтверждает freshness, blockers и право публикации.

## Failure Meaning

Post должен быть заблокирован, чтобы избежать небезопасного или устаревшего authoritative state.

## Used By

`PostToDefault`, защита stale approval и pre-post gate для package в Release 2.
