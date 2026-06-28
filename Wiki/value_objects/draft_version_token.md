---
title: Draft Version Token
type: value-object
status: planned
created: 2026-06-28
updated: 2026-06-28
source: RAW_inputs/meetings/persisted_edit_slice_EditVersion.md
tags: [domain-knowledge, value-object, edit-version, concurrency]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/aggregates/edit_version]
---

# Draft Version Token

`DraftVersionToken` - concurrency token текущего draft-состояния `EditVersion`.

## Equality

Равенство определяется конкретным token/moment, который client прочитал перед save. Если save приходит со старым token, команда должна считаться stale draft и требовать refresh.

## Not A Baseline Fact

`DraftVersionToken` не является `baseNetworkRevision` и не описывает authoritative `Default`. Drift `Default` относительно baseline обрабатывается позже на reconcile/post boundary.

## Immutability

Token не изменяется внутри уже выполненной команды save. После успешного persisted edit система может выдать новый token/moment для следующего draft update.

## Used By

`UpdateEditVersionFeatureGeometry`, optimistic concurrency и readback persisted edit slice.
