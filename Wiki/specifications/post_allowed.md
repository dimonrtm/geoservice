---
title: Post Allowed
type: specification
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, specification, post]
confidence: medium
related: [Wiki/commands/post_to_default, Wiki/policies/stale_approval_policy, Wiki/policies/reviewer_post_policy]
---

# Post Allowed

## Predicate

Package approved, не stale, hard blockers отсутствуют, текущий `Default` все еще соответствует reconcile/post assumptions, а evidence выполняет требования risk tier.

## Failure Meaning

Post должен быть заблокирован, чтобы избежать небезопасного или устаревшего authoritative state.

## Used By

`PostToDefault`, защита stale approval и pre-post gate для package в Release 2.
