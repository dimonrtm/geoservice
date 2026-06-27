---
title: Edit Version Feature Updated
type: domain-event
status: planned
created: 2026-06-27
updated: 2026-06-27
source: RAW_inputs/meetings/increment_after_open_workspace.md
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/commands/update_edit_version_feature, Wiki/entities/edit_version, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Feature Updated

## Source Aggregate

`EditVersion`.

## Happened In The Past

`UpdateEditVersionFeature` успешно сохранил изменение существующего feature внутри open `EditVersion`. В workspace появился настоящий persisted change set, а не только UI draft.

## Downstream Reactions

- Workspace response должен возвращать обновленное состояние feature и `operation=updated`.
- Smoke path может расшириться до edit-save-readback.
- `ReviewPackage` остается downstream artifact и создается только после появления persisted changes и последующих readiness predicates.
