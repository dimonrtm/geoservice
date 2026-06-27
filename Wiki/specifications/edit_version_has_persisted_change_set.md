---
title: Edit Version Has Persisted Change Set
type: specification
status: planned
created: 2026-06-27
updated: 2026-06-27
source: RAW_inputs/meetings/increment_after_open_workspace.md
tags: [domain-knowledge, specification, edit-version, workspace]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature, Wiki/specifications/edit_version_ready_for_review]
---

# Edit Version Has Persisted Change Set

## Predicate

`EditVersion` имеет хотя бы одно сохраненное изменение в version-scoped workspace: `operation=updated`, `created` или `deleted` на feature/association row. Для ближайшего инкремента минимальный достаточный случай - `operation=updated` на существующем feature.

## Failure Meaning

Workspace пока остается read-only витриной или UI draft без доменного change set. Draft validation, submit и `ReviewPackage` будут преждевременными, если они не могут опереться на persisted changes.

## Used By

Draft validation, readiness predicates, будущий `SubmitForReview`, smoke edit-save-readback и построение `ReviewPackage v0.1`.
