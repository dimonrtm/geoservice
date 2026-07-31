---
title: Policies Registry
type: index
status: active
created: 2026-06-24
updated: 2026-07-31
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, policy]
confidence: n/a
related: [Wiki/index]
---

# Policies Registry

| Policy | Rule | Decision Outcome | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/policies/edit_geometry_precision_policy]] | Канонизировать server-side только изменённую вершину по metadata сохраняющего dataset, затем проверить hard guards; не выполнять скрытый snapping или full-line renormalization. | changed/no-op/rejected | high | `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/policies/positional_accuracy_acceptance_policy]] | Разрешить technical save с `POSITIONAL_ACCURACY_UNVERIFIED`, но требовать утверждённую specification и independent evidence до review/completion/post. | verified/unverified/exceeded | high | `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/policies/reviewer_post_policy]] | `Reviewer` принимает `approve package`, `return for changes`, `request evidence` или `escalate`; stale/block вычисляет система. | approved/returned/evidence_requested/escalated | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/policies/stale_approval_policy]] | Изменения `Default`, geometry, association, network attribute, terminal config, validation, trace/subnetwork или evidence делают approval устаревшим. | Repeat review или recompute package | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
