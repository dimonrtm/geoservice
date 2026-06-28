---
title: Edit Version Basic Draft Validation
type: specification
status: planned
created: 2026-06-28
updated: 2026-06-28
source: RAW_inputs/meetings/persisted_edit_slice_EditVersion.md
tags: [domain-knowledge, specification, edit-version, validation]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_ready_for_review, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Version Basic Draft Validation

## Predicate

После first save система синхронно вычисляет дешевую draft validation для persisted geometry diff:

- `geometryValid`
- `aoiOk`
- `associationsUnchanged`
- `topologyNotChecked`
- `dirtyRelativeToBaseline`
- optional `concurrencyOk`

Эта проверка подтверждает инварианты сохранения `EditVersion`, но не заменяет full topology validation, reconcile, review или post readiness.

## Failure Meaning

Persisted draft change set не может считаться пригодным для следующего шага workflow. Editor должен исправить геометрию, AOI/scope violation, stale draft или случайное изменение association/endpoints до продолжения.

## Used By

Edit-save-readback slice, `EditVersionReadyForReview`, будущий `SubmitForReview` и построение `ReviewPackage` после появления устойчивого change set.
