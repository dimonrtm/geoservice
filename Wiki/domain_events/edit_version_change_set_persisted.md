---
title: Edit Version Change Set Persisted
type: domain-event
status: planned
created: 2026-06-28
updated: 2026-07-25
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature_geometry, Wiki/domain_events/edit_version_change_set_cleared, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Change Set Persisted

## Source Aggregate

`EditVersion`.

## Happened In The Past

`UpdateEditVersionFeatureGeometry` успешно сохранил content-changing resulting geometry существующей line feature, и текущий diff относительно immutable baseline остался непустым. Событие возникает после каждого успешного save с непустым diff: как при переходе `unchanged -> updated`, так и при `updated -> updated`.

No-op save и идемпотентный retry уже выполненного `CommandId` не создают событие. Если editor возвращает geometry к baseline и persisted change set становится пустым, возникает [[Wiki/domain_events/edit_version_change_set_cleared]].

## Suggested Payload

- `editVersionId`
- `featureId`
- `baselineRevisionRef`
- `newDraftVersionToken`
- `operation`
- `hasPersistedChangeSet`
- `basicValidation`
- `geometryHash` или `bbox`

## Downstream Reactions

- Read model и audit могут зафиксировать очередное persisted draft state без подмены current diff историей save attempts.
- Workspace/readback показывает resulting feature, `hasPersistedChangeSet`, новый token и computed diff относительно baseline.
- `SubmitForReview` и `ReviewPackage` остаются downstream и не появляются до устойчивого persisted edit slice.
