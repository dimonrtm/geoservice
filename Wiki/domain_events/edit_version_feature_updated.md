---
title: Edit Version Feature Updated
type: domain-event
status: superseded
created: 2026-06-27
updated: 2026-06-28
source: "RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, domain-event, edit-version, workspace]
confidence: high
related: [Wiki/domain_events/edit_version_change_set_persisted, Wiki/commands/update_edit_version_feature_geometry, Wiki/entities/edit_version, DDD_Wiki/aggregates/edit_version]
---

# Edit Version Feature Updated

## Status

Superseded by [[Wiki/domain_events/edit_version_change_set_persisted]] for the first persisted edit slice. The old name is too feature-update centric and hides the domain fact that matters now: a persisted change set appeared in `EditVersion`.

## Source Aggregate

`EditVersion`.

## Happened In The Past

Старое событие описывало сохранение feature update слишком широко. Для первого slice используется событие о persisted change set.

## Downstream Reactions

- События review/post остаются downstream и не заменяют факт persisted change set.
