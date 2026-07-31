---
title: Utility Editor Workflow
type: use-case
status: active
created: 2026-06-24
updated: 2026-07-31
source: "Vision_wiki/decisions/release_1_utility_workflow.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, ddd, use-case]
confidence: high
related: [Wiki/glossary/utility_gis_editing, Wiki/commands/open_edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/policies/positional_accuracy_acceptance_policy, Wiki/commands/post_to_default]
---

# Utility Editor Workflow

## Scenario

`Editor` входит в систему, видит назначенную `WorkOrder`, открывает `EditVersion`, работает внутри изолированного workspace, выполняет validation/reconcile изменений, разрешает conflicts, отправляет package на review, получает semantic approval, проходит computed pre-post gate, а технически разрешенный result публикуется в authoritative `Default` через `Publisher` / system `post-gate` с audit.

## Current Implemented Slice

Sprint 1 покрывает login, список назначенных `WorkOrder`, открытие `EditVersion` и загрузку workspace. Следующий code-aware slice расширяет путь до edit-save-readback-revert:

1. Открыть `EditVersion` и получить `DraftVersionToken`.
2. Выбрать одну существующую line feature минимум с тремя вершинами, целиком `covered by` AOI.
3. Сдвинуть ровно одну внутреннюю вершину.
4. Сохранить full resulting geometry с `CommandId`, если hard invariants выполнены; отсутствие positional evidence не блокирует technical save, а фиксируется как `POSITIONAL_ACCURACY_UNVERIFIED`.
5. Получить server-canonical `updatedFeature`, новый token, `operation`, `hasPersistedChangeSet` и `basicValidation`.
6. Повторным readback после restart подтвердить persisted state.
7. Вернуть geometry к baseline и подтвердить `operation=unchanged` и `EditVersionChangeSetCleared`.

## Planned Slices

Следующий integrated review/post путь должен быть встроен в текущий `WorkOrder` / `EditVersion` flow, но только после persisted change set. First-save stop-line означает `persisted-draft-ready`, а не review-ready: `EditVersion` остается `open`, `WorkOrder` - `open/in_progress`, `topologyChecked=not_checked`. Перед review/completion/post требуется `POSITIONAL_ACCURACY_VERIFIED` по утверждённой спецификации и evidence. Затем идут `submit_for_review`, package build, reviewer decision, computed `can_post`, simulated post и durable audit. Планирование идет маленькими спринтами; старый standalone Release 2 implementation contract остается reference/legacy source, а не текущим implementation source of truth.
