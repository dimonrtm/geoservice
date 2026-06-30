---
title: Draft Version Token
type: value-object
status: planned
created: 2026-06-28
updated: 2026-06-30
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md"
tags: [domain-knowledge, value-object, edit-version, concurrency]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/aggregates/edit_version]
---

# Draft Version Token

`DraftVersionToken` - opaque concurrency token версии всего агрегата `EditVersion`, а не version отдельной feature row и не hash текущего change set.

## Equality

Равенство определяется конкретным token/moment, который client прочитал перед save. Если save приходит со старым token, команда должна считаться stale draft и требовать refresh. Практическая форма может быть `rowversion`, monotonically increasing revision или ULID-with-revision.

## Changes On Aggregate Mutation

Token меняется после любой успешной persisted мутации внутри `EditVersion`: изменился change set, validation summary или metadata агрегата. Token защищает transactional consistency boundary агрегата, а не отдельную строку feature.

## Immutability

Уже выданный token не изменяется. После successful save система выдает новый opaque token для следующей команды; старый token остается историческим значением и не должен переиспользоваться как актуальный.

## Not A Baseline Fact

`DraftVersionToken` не является `baseNetworkRevision`, не описывает authoritative `Default` и не доказывает свежесть относительно Default. `networkVersion` / baseline network revision, если хранится в draft row, должен трактоваться как baseline-факт common ancestor для future stale/conflict logic, а не как optimistic concurrency token. Drift `Default` относительно baseline обрабатывается позже на reconcile/post boundary.

## Idempotency

Повторный запрос со старым token после successful save по смыслу является stale. Хороший retry UX нужно поддерживать отдельным `CommandId` / idempotency key: тот же command может вернуть idempotent success, а другой запрос со старым token должен стать conflict.

## Used By

`UpdateEditVersionFeatureGeometry`, optimistic concurrency и readback persisted edit slice.
