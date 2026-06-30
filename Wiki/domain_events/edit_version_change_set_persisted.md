---
title: Edit Version Change Set Persisted
type: domain-event
status: planned
created: 2026-06-28
updated: 2026-06-30
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Change Set Persisted

## Source Aggregate

`EditVersion`.

## Happened In The Past

`UpdateEditVersionFeatureGeometry` успешно перевел `EditVersion` из `unchanged` в `updated`: в версии впервые появился ненулевой persisted change set для geometry-only изменения существующей линии. Важен state transition, а не каждый технический save. Повторный identical retry не создает новое событие.

Если editor возвращает geometry к baseline и persisted change set становится пустым, это другой факт модели: будущий `EditVersionChangeSetCleared` может фиксировать переход `updated -> unchanged`. `EditVersionChangeSetPersisted` не должен подменять audit history промежуточных save attempts.

## Suggested Payload

- `editVersionId`
- `featureId`
- `baselineFeatureRef`
- `operation`
- `changedSurface = geometry`
- `validationFlags`
- `draftVersionToken`
- `editorId`
- `occurredAt`

## Downstream Reactions

- Workspace/readback может показать resulting feature, `hasPersistedChangeSet`, новый token и computed diff относительно baseline.
- Basic draft validation может опереться на уже сохраненный change set.
- `SubmitForReview` и `ReviewPackage` остаются downstream и не появляются до устойчивого persisted edit slice.
