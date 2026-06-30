---
title: Edit Version Has Persisted Change Set
type: specification
status: planned
created: 2026-06-27
updated: 2026-06-30
source: "RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
tags: [domain-knowledge, specification, edit-version, workspace]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_basic_draft_validation, Wiki/specifications/edit_version_ready_for_review]
---

# Edit Version Has Persisted Change Set

## Predicate

`EditVersion` имеет хотя бы один сохраненный material diff относительно baseline в разрешенной поверхности редактирования. Для ближайшего инкремента разрешенная поверхность - только geometry-only изменение существующей line `NetworkFeature`: сдвиг внутренней вершины или внутренних вершин без изменения endpoints, `part count`, vertex identity и associations.

`operation=updated` означает текущее persisted-отличие от baseline, а не факт, что пользователь когда-то нажимал save. Если пользователь вернул feature к baseline и diff стал пустым, persisted projection должна нормализоваться обратно к `unchanged`; история действия относится к audit/event stream, а не к `operation`.

Source of truth для predicate - baseline snapshot и full resulting feature snapshot. Diff вычисляется между ними как производный артефакт и может кэшироваться позже для review package, но не должен быть единственной persisted формой.

Минимальное доказательство этого predicate - не `success=true`, а resulting feature snapshot + `hasPersistedChangeSet=true` + validation flags после save. Explicit baseline diff полезен для readback/review, но не является обязательным minimum proof первого save.

## Failure Meaning

Workspace пока остается read-only витриной или UI draft без доменного change set. Draft validation, submit и `ReviewPackage` будут преждевременными, если они не могут опереться на persisted changes.

## Used By

Computed diff, [[Wiki/specifications/edit_version_basic_draft_validation]], readiness predicates, будущий `SubmitForReview`, smoke edit-save-readback и построение `ReviewPackage v0.1`.
