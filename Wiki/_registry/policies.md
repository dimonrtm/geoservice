---
title: Policies Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, policy]
confidence: n/a
related: [Wiki/index]
---

# Policies Registry

| Policy | Rule | Decision Outcome | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/policies/reviewer_post_policy]] | `Reviewer` approves package; `Publisher` / demo-system action выполняет technical post. | approved/rejected/escalated/stale/blocked | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| [[Wiki/policies/stale_approval_policy]] | Изменения `Default`, geometry, association, network attribute, terminal config, validation, trace/subnetwork или evidence делают approval устаревшим. | Repeat review или recompute package | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
