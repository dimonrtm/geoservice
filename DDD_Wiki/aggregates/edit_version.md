---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-07-31
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/glossary/base_work_state, Wiki/policies/edit_geometry_precision_policy, Wiki/policies/positional_accuracy_acceptance_policy, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/draft_version_token, Wiki/value_objects/command_id, DDD_Wiki/invariants/edit_version_persisted_edit_invariants, DDD_Wiki/state_machines/edit_version_persisted_change_set, DDD_Wiki/state_machines/edit_version_save_request]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

Текущий реализованный slice трактует workspace как read-only после открытия. Следующий обязательный slice делает `EditVersion` consistency boundary атомарного save: агрегат хранит единое immutable [[Wiki/glossary/base_work_state]], full current snapshot одной изменяемой line feature, aggregate-level `DraftVersionToken`, idempotency record по `CommandId` и `basicValidation`. Diff, `operation` и `hasPersistedChangeSet` вычисляются относительно базового состояния работы. `ReviewPackage` и `submit_for_review` не появляются раньше persisted change set.

## Protected Invariants

- `baseNetworkRevision` неизменяем после создания.
- `baseNetworkRevision` / `BaselineRevisionRef` задаёт единое базовое состояние всей назначенной работы; feature-level `networkVersion` остаётся историей линии и не является отдельным baseline.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
- Непустой first-slice change set содержит geometry только одной существующей line feature во всей версии и отличается от baseline ровно одной внутренней вершиной. Resulting geometry, равная baseline, отдельно допустима как revert; endpoint move, изменение остальных координат, vertex insert/delete, split/merge, `part count` change, create/delete, attributes и association mutation запрещены.
- Resulting line валидна, проста и целиком `covered by` AOI; граница AOI допустима.
- `operation` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` является version всего агрегата, выдается при read/open и меняется только на content-changing mutation; no-op/read/refresh его не меняют.
- `CommandId` обязателен: одинаковый id + canonical payload fingerprint присоединяется к одной operation и возвращает её состояние/результат, другой fingerprint с тем же id отклоняется. Операционный record живёт весь lifecycle `EditVersion`, переживает reconnect/relogin/device switch и запоминает domain rejection; долгосрочная append-only history хранится отдельно.
- После закрытия save context старый retry отклоняется и не трактуется как новая команда. Точный срок хранения immutable operation history остаётся открытым records-policy выбором.
- Stale token и hard-invariant failure отклоняют mutation атомарно; stale error возвращает актуальные persisted object и token.
- `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff; revert создает `EditVersionChangeSetCleared`; no-op и retry событий не создают.
- История каждого content-changing save хранит line identity, before/after geometry, editor, time, базовое состояние и `CommandId`; current diff является отдельной materialized projection.
- Draft summary/evidence могут жить рядом с `EditVersion` до submit; durable review snapshot создается позже в `ReviewPackage`.
- `POSITIONAL_ACCURACY_UNVERIFIED` допускается в technical working draft, но блокирует downstream review/completion/post; storage grid и positional acceptance остаются разными правилами.
