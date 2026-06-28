---
title: Edit Version Has Persisted Change Set
type: specification
status: planned
created: 2026-06-27
updated: 2026-06-28
source: "RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, specification, edit-version, workspace]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_basic_draft_validation, Wiki/specifications/edit_version_ready_for_review]
---

# Edit Version Has Persisted Change Set

## Predicate

`EditVersion` имеет хотя бы один сохраненный diff относительно baseline в разрешенной поверхности редактирования. Для ближайшего инкремента разрешенная поверхность - только geometry diff существующей line `NetworkFeature`, предпочтительно сдвиг внутренней вершины без изменения endpoints и associations.

`operation=updated` означает текущее persisted-отличие от baseline, а не факт, что пользователь когда-то нажимал save. Если пользователь вернул feature к baseline и diff стал пустым, persisted projection должна нормализоваться обратно к `unchanged`; история действия относится к audit/event stream, а не к `operation`.

## Failure Meaning

Workspace пока остается read-only витриной или UI draft без доменного change set. Draft validation, submit и `ReviewPackage` будут преждевременными, если они не могут опереться на persisted changes.

## Used By

Readback diff, [[Wiki/specifications/edit_version_basic_draft_validation]], readiness predicates, будущий `SubmitForReview`, smoke edit-save-readback и построение `ReviewPackage v0.1`.
