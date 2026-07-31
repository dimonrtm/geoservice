---
title: Value Objects Registry
type: index
status: active
created: 2026-06-24
updated: 2026-07-31
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, value-object]
confidence: n/a
related: [Wiki/index]
---

# Value Objects Registry

| Value Object | Equality | Used By | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/value_objects/aoi]] | scope id + geometry в контексте `WorkOrder`; first-save line должна быть `covered by`, boundary разрешена | [[Wiki/entities/work_order]], [[Wiki/commands/update_edit_version_feature_geometry]] | high | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md`; `RAW_inputs/meetings/first_save_for_edit_version.md` |
| [[Wiki/value_objects/draft_version_token]] | opaque strong validator всего aggregate `EditVersion`; не baseline/Default freshness и не idempotency key | [[Wiki/entities/edit_version]] | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md` |
| [[Wiki/value_objects/command_id]] | одинаковый глобальный id равен одной operation только при совпадении lifecycle context и canonical fingerprint; registry живёт весь lifecycle `EditVersion` | [[Wiki/commands/update_edit_version_feature_geometry]] | high | `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/value_objects/risk_tier]] | Значение tier + подтверждающие факты | [[Wiki/entities/review_decision]] | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
