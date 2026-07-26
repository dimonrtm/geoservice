---
title: Update Edit Version Feature Geometry
type: command
status: planned
created: 2026-06-28
updated: 2026-07-26
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md"
tags: [domain-knowledge, command, edit-version, workspace, geometry]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/glossary/base_work_state, Wiki/glossary/coordinate_storage_precision, Wiki/policies/edit_geometry_precision_policy, Wiki/value_objects/aoi, Wiki/value_objects/draft_version_token, Wiki/value_objects/command_id, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation, Wiki/domain_events/edit_version_change_set_persisted, Wiki/domain_events/edit_version_change_set_cleared, DDD_Wiki/aggregates/edit_version]
---

# Update Edit Version Feature Geometry

## Actor

`Editor`, назначенный на `WorkOrder`.

## Target

Существующая line `NetworkFeature` внутри open `EditVersion` текущего `WorkOrder` workspace.

## Intent

Заменить текущую persisted geometry существующей line `NetworkFeature` на переданную full resulting geometry внутри `EditVersion`. Команда выражает итоговый shape, а не UI-операцию или diff. Guard первого slice разрешает непустой diff только одного класса — сдвиг ровно одной внутренней вершины — и отдельно допускает resulting geometry, равную baseline, для revert.

## Preconditions

- `Editor` назначен на `WorkOrder`.
- `EditVersion` существует, имеет статус `open` и принадлежит этой `WorkOrder`.
- Target feature существует в immutable baseline этой версии, является line geometry минимум с тремя вершинами и доступен в workspace.
- Во всей `EditVersion` изменяется не больше одной существующей line feature.
- Позиционная точность для приёмки берётся из спецификации задания/продукта данных; шаг coordinate normalization — из настроек слоя/БД.
- Перемещённая вершина детерминированно канонизируется к dataset precision/grid. После канонизации resulting geometry либо равна baseline, либо отличается от неё ровно одной внутренней вершиной; все остальные координаты совпадают с baseline и не перенормализуются.
- Start/end vertices, feature identity, association semantics, create/delete, split/merge, attributes, `part count`, vertex count и insert/delete vertex не меняются.
- Resulting geometry валидна и проста, а вся линия `covered by` AOI; касание границы AOI допустимо.
- `DraftVersionToken` совпадает с текущей версией агрегата `EditVersion`; устаревший token означает stale draft и требует refresh.
- `CommandId` обязателен и уникально обозначает canonical payload fingerprint: target feature, базовое состояние работы, ожидаемый `DraftVersionToken`, тип операции, изменяемую вершину и resulting geometry после coordinate normalization.

## Outcome

При допустимом изменении система атомарно сохраняет full resulting geometry snapshot рядом с immutable baseline snapshot. Diff вычисляется как read model. Командный ответ содержит `updatedFeature`, новый `draftVersionToken`, `operation`, `hasPersistedChangeSet` и `basicValidation`; отдельный readback должен вернуть тот же persisted state и пережить restart browser/backend.

- Непустой diff дает `operation=updated`, `hasPersistedChangeSet=true` и [[Wiki/domain_events/edit_version_change_set_persisted]] на каждый успешный content-changing save.
- Revert к baseline сохраняет current snapshot равным baseline, дает `operation=unchanged`, `hasPersistedChangeSet=false`, меняет token и создает [[Wiki/domain_events/edit_version_change_set_cleared]].
- No-op относительно текущего persisted state не меняет token и не создает событие.
- Повтор с тем же `CommandId` и тем же fingerprint возвращает результат уже выполненной команды без новой мутации и нового события; переиспользование `CommandId` для другого fingerprint отклоняется. Если feature после исходной команды менялась снова, response также показывает актуальный persisted object.
- Stale `DraftVersionToken` отклоняет mutation и возвращает актуальные persisted object и token для refresh/merge.
- Нарушение hard invariants отклоняет save атомарно; запрещенное состояние не сохраняется как blocked draft.

## Out Of Scope

Create/delete feature, point/device/junction editing, изменение attributes, endpoint connectivity, vertex insert/delete, split/merge, association mutation, containment/attachment changes, multi-feature change set, full-line renormalization, shared-node/topological editing, topology validate/trace, live-`Default` freshness check, reconcile, submit for review, `ReviewPackage`, `can_post`, post и review conflict UI.
