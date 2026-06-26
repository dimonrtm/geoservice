---
title: Conflicts Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-26
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, conflict]
confidence: n/a
related: [Wiki/index, DDD_Wiki/model_health]
---

# Conflicts Registry

| Conflict | Blocks | Status | Question | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | Модель ролей и прав для финальной публикации | resolved | `Publisher` - отдельная technical role; v0.1 использует system `post-gate`; `Reviewer` - semantic approval | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | Единая state machine review/post и границы спринта | resolved | Must для ближайшего slice: `ReviewPackage`, evidence, risk tier, absolute veto, stale, computed `can_post`, simulated post, audit | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | Source of truth для нового review/post implementation contract | resolved | Новый contract отдельный и встроенный в `WorkOrder` / `EditVersion` flow; старый artifact - legacy/reference | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; user chat 2026-06-26 |
