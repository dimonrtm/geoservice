---
title: Edit Version Change Set Cleared
type: domain-event
status: planned
created: 2026-07-25
updated: 2026-07-26
source: "RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md"
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature_geometry, Wiki/domain_events/edit_version_change_set_persisted, Wiki/specifications/edit_version_has_persisted_change_set, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Change Set Cleared

## Source Aggregate

`EditVersion`.

## Happened In The Past

`UpdateEditVersionFeatureGeometry` успешно сохранил current snapshot, равный immutable baseline. Текущий change set исчез: `operation=unchanged`, `hasPersistedChangeSet=false`. Агрегат реально изменился относительно предыдущего persisted state, поэтому `DraftVersionToken` сменился.

No-op save уже неизменного baseline state и идемпотентный retry не создают это событие.

## Suggested Payload

- `editVersionId`
- `featureId`
- `commandId`
- `baselineRevisionRef`
- `beforeGeometry`
- `afterGeometry` = baseline geometry
- `editorId`
- `occurredAt`
- `newDraftVersionToken`
- `operation=unchanged`
- `hasPersistedChangeSet=false`
- `basicValidation`
- `bbox` и `geometryHash` необязательны и не заменяют before/after evidence.

## Downstream Reactions

- Read model удаляет current diff и показывает неизменное состояние.
- Audit сохраняет неизменяемый before/after факт «редактировали, затем вернули к baseline», не загрязняя current domain state.
- Submit/review остается недоступным, пока не появится новый persisted change set.
