---
title: Edit Version Basic Draft Validation
type: specification
status: planned
created: 2026-06-28
updated: 2026-07-26
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md"
tags: [domain-knowledge, specification, edit-version, validation]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_ready_for_review, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Version Basic Draft Validation

## Predicate

После first save система синхронно вычисляет small validation summary со статусами `passed`, `failed` и `not_checked`:

До вычисления summary перемещённая вершина детерминированно канонизируется к [[Wiki/glossary/coordinate_storage_precision]]. Нетронутые вершины не перенормализуются. Если канонический результат совпал с текущим persisted state, команда является no-op; если канонизация дала невалидную, непростую или схлопнутую линию, команда отклоняется атомарно.

| Поле | Успешный save | Значение |
| --- | --- | --- |
| `geometryValid` | `passed` | Resulting geometry имеет допустимый line type, валидна и проста; `part count`, vertex count и endpoints относительно baseline не изменились. |
| `aoiCovered` | `passed` | Вся resulting line `covered by` AOI; касание границы допустимо. |
| `associationsUnchanged` | `passed` | Command surface не меняет associations; это evidence соблюденного hard invariant. |
| `topologyChecked` | `not_checked` | Full topology validation остается отдельным downstream этапом. |
| `dirtyRelativeToBaseline` | `passed` для непустого diff; `failed`/false после revert | Информационный статус текущего отличия, а не критерий качества. |
| `concurrencyOk` | `passed` | Команда применена к актуальному `DraftVersionToken`; при stale token mutation не выполняется. |

Нарушение `geometryValid`, `aoiCovered`, structure/endpoints или association invariants отклоняет save атомарно, поэтому persisted successful result не содержит `failed` hard-invariant state. Summary подтверждает persisted draft, но не заменяет topology validation, reconcile, review или post readiness.

## Failure Meaning

Команда отклоняется без изменения агрегата. Editor должен исправить geometry validity, AOI coverage, stale draft, endpoint move, vertex insert/delete, split/merge, попытку изменить более одной внутренней вершины или association/attribute mutation.

## Used By

Edit-save-readback slice, `EditVersionReadyForReview`, будущий `SubmitForReview` и построение `ReviewPackage` после появления устойчивого change set.
