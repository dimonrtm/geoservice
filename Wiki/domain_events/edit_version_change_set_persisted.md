---
title: Edit Version Change Set Persisted
type: domain-event
status: planned
created: 2026-06-28
updated: 2026-06-28
source: RAW_inputs/meetings/persisted_edit_slice_EditVersion.md
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_has_persisted_change_set, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Change Set Persisted

## Source Aggregate

`EditVersion`.

## Happened In The Past

`UpdateEditVersionFeatureGeometry` успешно сохранил ненулевой geometry diff существующей линии относительно baseline внутри open `EditVersion`. В версии появился persisted change set, а не только UI draft или техническая квитанция save.

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

- Workspace/readback может показать persisted feature и diff относительно baseline.
- Basic draft validation может опереться на уже сохраненный change set.
- `SubmitForReview` и `ReviewPackage` остаются downstream и не появляются до устойчивого persisted edit slice.
