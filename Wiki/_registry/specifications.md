---
title: Specifications Registry
type: index
status: active
created: 2026-06-24
updated: 2026-07-31
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, specification]
confidence: n/a
related: [Wiki/index]
---

# Specifications Registry

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/editor_assigned_to_work_order]] | Текущий активный editor является назначенным исполнителем. | Нельзя открыть edit version/workspace. | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/specifications/edit_version_has_persisted_change_set]] | В `EditVersion` есть current diff одной line feature и одной внутренней вершины относительно базового состояния работы; response + durable readback доказывают persisted state. | Workspace пока read-only или UI-only draft; submit/review преждевременны. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md` |
| [[Wiki/specifications/edit_version_basic_draft_validation]] | First save канонизирует изменённую вершину, проверяет hard guards и отдельно фиксирует `POSITIONAL_ACCURACY_UNVERIFIED`, пока нет specification/evidence. | Hard failure отклоняет save атомарно; unverified positional status разрешает working draft, но не review. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/specifications/edit_version_ready_for_review]] | Persisted change set, basic draft validation, `POSITIONAL_ACCURACY_VERIFIED`, freshness/evidence, затем полный reconcile/default predicate. | Review преждевременен или blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/specifications/post_allowed]] | Computed `can_post`: package approved, not stale, no absolute veto, `Default` fresh, required evidence complete, pre-post gate passed. | Simulated/technical post blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
