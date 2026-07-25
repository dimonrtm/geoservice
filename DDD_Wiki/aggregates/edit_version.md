---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-07-25
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/draft_version_token, Wiki/value_objects/command_id, DDD_Wiki/invariants/edit_version_persisted_edit_invariants, DDD_Wiki/state_machines/edit_version_persisted_change_set]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

Текущий реализованный slice трактует workspace как read-only после открытия. Следующий обязательный slice делает `EditVersion` consistency boundary атомарного save: агрегат хранит immutable baseline snapshot, full current snapshot одной изменяемой line feature, aggregate-level `DraftVersionToken`, idempotency record по `CommandId` и `basicValidation`. Diff, `operation` и `hasPersistedChangeSet` вычисляются относительно baseline. `ReviewPackage` и `submit_for_review` не появляются раньше persisted change set.

## Protected Invariants

- `baseNetworkRevision` неизменяем после создания.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
- Непустой first-slice change set содержит geometry только одной существующей line feature во всей версии и отличается от baseline ровно одной внутренней вершиной. Resulting geometry, равная baseline, отдельно допустима как revert; endpoint move, изменение остальных координат, vertex insert/delete, split/merge, `part count` change, create/delete, attributes и association mutation запрещены.
- Resulting line валидна, проста и целиком `covered by` AOI; граница AOI допустима.
- `operation` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` является version всего агрегата, выдается при read/open и меняется только на content-changing mutation; no-op/read/refresh его не меняют.
- `CommandId` обязателен: одинаковый id + payload дает idempotent success, другой payload с тем же id отклоняется.
- Stale token и hard-invariant failure отклоняют mutation атомарно; stale error возвращает актуальные persisted object и token.
- `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff; revert создает `EditVersionChangeSetCleared`; no-op и retry событий не создают.
- Draft summary/evidence могут жить рядом с `EditVersion` до submit; durable review snapshot создается позже в `ReviewPackage`.
