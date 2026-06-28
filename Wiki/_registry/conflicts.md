---
title: Conflicts Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-28
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, conflict]
confidence: n/a
related: [Wiki/index, DDD_Wiki/model_health]
---

# Conflicts Registry

| Conflict | Blocks | Status | Question | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | Модель ролей и прав для финальной публикации | resolved | `Publisher` - отдельная technical role; v0.1 использует system `post-gate`; `Reviewer` - semantic approval | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | Единая state machine review/post и границы спринта | resolved | Review/post остается must для downstream slice, но не раньше persisted edit change set | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/increment_after_open_workspace.md` |
| [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | Source of truth для нового review/post implementation contract | resolved | Новый contract отдельный и встроенный в `WorkOrder` / `EditVersion` flow; старый artifact - legacy/reference | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; user chat 2026-06-26 |
| [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] | Sprint planning после открытия workspace | resolved | Сначала persisted geometry diff существующей линии + edit-save-readback + basic draft validation; review/post layers откладываются | `RAW_inputs/meetings/increment_after_open_workspace.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md` |
