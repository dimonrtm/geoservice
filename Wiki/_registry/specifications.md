---
title: Specifications Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-26
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, specification]
confidence: n/a
related: [Wiki/index]
---

# Specifications Registry

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/editor_assigned_to_work_order]] | Текущий активный editor является назначенным исполнителем. | Нельзя открыть edit version/workspace. | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/specifications/edit_version_ready_for_review]] | Последний reconcile с текущим `Default`, нет unresolved conflicts, validation clean от veto, evidence и editor summary готовы. | Review преждевременен или blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/specifications/post_allowed]] | Computed `can_post`: package approved, not stale, no absolute veto, `Default` fresh, required evidence complete, pre-post gate passed. | Simulated/technical post blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
