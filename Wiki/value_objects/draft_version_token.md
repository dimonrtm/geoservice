---
title: Draft Version Token
type: value-object
status: planned
created: 2026-06-28
updated: 2026-07-25
source: "RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, value-object, edit-version, concurrency]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/command_id, DDD_Wiki/aggregates/edit_version]
---

# Draft Version Token

`DraftVersionToken` - opaque concurrency token версии всего агрегата `EditVersion`, а не version отдельной feature row и не hash текущего change set.

## Equality

Равенство определяется конкретным opaque strong validator, который client получил при первом read/open `EditVersion`. Если save приходит со старым token, команда считается stale draft и не меняет агрегат.

## Changes On Aggregate Mutation

Token меняется только после content-changing persisted mutation внутри `EditVersion`: current geometry snapshot или change set создан, обновлен или очищен; validation summary изменился как следствие save; lifecycle/status изменился. `lastOpenedAt`, refresh, read и повторный расчет того же результата token не меняют. No-op save относительно текущего persisted state также не меняет token.

## Immutability

Уже выданный token не изменяется. После successful save система выдает новый opaque token для следующей команды; старый token остается историческим значением и не должен переиспользоваться как актуальный.

## Not A Baseline Fact

`DraftVersionToken` не является `baseNetworkRevision`, не описывает authoritative `Default` и не доказывает свежесть относительно Default. `networkVersion` / baseline network revision, если хранится в draft row, должен трактоваться как baseline-факт common ancestor для future stale/conflict logic, а не как optimistic concurrency token. Drift `Default` относительно baseline обрабатывается позже на reconcile/post boundary.

## Idempotency

Повторный запрос со старым token после successful save по смыслу является stale. [[Wiki/value_objects/command_id]] отделяет idempotent retry от concurrency: тот же `CommandId` с тем же payload возвращает idempotent success, а другой запрос со старым token становится conflict. Error payload stale-команды возвращает актуальные persisted object и token для refresh/merge.

## Used By

`UpdateEditVersionFeatureGeometry`, optimistic concurrency и readback persisted edit slice.
