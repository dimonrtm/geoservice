---
title: Specifications Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-30
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, specification]
confidence: n/a
related: [Wiki/index]
---

# Specifications Registry

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/editor_assigned_to_work_order]] | Текущий активный editor является назначенным исполнителем. | Нельзя открыть edit version/workspace. | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/specifications/edit_version_has_persisted_change_set]] | В `EditVersion` есть material diff относительно baseline; первый минимум доказан resulting feature snapshot + `hasPersistedChangeSet` + validation flags, explicit diff является производным. | Workspace пока read-only или UI-only draft; submit/review преждевременны. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| [[Wiki/specifications/edit_version_basic_draft_validation]] | First save синхронно подтверждает `geometryValid`, `insideAoi`, `associationsUnchanged`, `topologyNotChecked`, `dirtyRelativeToBaseline` и optional `concurrencyOk`. | Draft change set не годится для следующего workflow step. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md` |
| [[Wiki/specifications/edit_version_ready_for_review]] | Persisted change set, basic draft validation, freshness/evidence, затем полный reconcile/default predicate. | Review преждевременен или blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md` |
| [[Wiki/specifications/post_allowed]] | Computed `can_post`: package approved, not stale, no absolute veto, `Default` fresh, required evidence complete, pre-post gate passed. | Simulated/technical post blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
