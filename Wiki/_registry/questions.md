---
title: Questions Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-29
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, question]
confidence: n/a
related: [Wiki/index, DDD_Wiki/model_health]
---

# Questions Registry

| Question | Domain Gap | Priority | Status | Answer Source |
| --- | --- | --- | --- | --- |
| `Publisher` - отдельная роль, ответственность data owner или техническая операция? | [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | high | answered | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| Какие правила Release 2 про устаревание и блокеры должны влиять на следующий 14-дневный спринт? | [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | high | answered | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| Новый review/post contract должен обновлять legacy artifact или быть отдельным integrated artifact? | [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | high | answered | user chat 2026-06-26 |
| Где должен заканчиваться ближайший review/post slice? | [[DDD_Wiki/use_cases/utility_editor_workflow]] | high | answered | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| `can_post` должен быть persisted state или computed specification? | [[Wiki/specifications/post_allowed]] | high | answered | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| Какой ближайший полноценный инкремент после открытия workspace? | [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] | high | answered | `RAW_inputs/meetings/increment_after_open_workspace.md` |
| Что должно предшествовать `ReviewPackage` в текущем кодовом flow? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/increment_after_open_workspace.md` |
| Что считать первым persisted change в `EditVersion`? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| Как должна называться первая команда сохранения feature change? | [[Wiki/commands/update_edit_version_feature_geometry]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| Какие инварианты и validation flags обязательны для first save? | [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| Где stop-line перед review/post после открытия workspace? | [[DDD_Wiki/use_cases/utility_editor_workflow]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| Что доказывает successful first save/readback? | [[Wiki/specifications/edit_version_has_persisted_change_set]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| Что означает `DraftVersionToken` / `networkVersion`? | [[Wiki/value_objects/draft_version_token]] | high | answered | `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
