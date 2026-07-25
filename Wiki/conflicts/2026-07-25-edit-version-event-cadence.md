---
title: Edit Version Event Cadence
type: conflict
status: resolved
created: 2026-07-25
updated: 2026-07-25
source: "RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md"
tags: [domain-knowledge, conflict, edit-version, domain-event]
confidence: high
related: [Wiki/domain_events/edit_version_change_set_persisted, Wiki/domain_events/edit_version_change_set_cleared, DDD_Wiki/state_machines/edit_version_persisted_change_set]
---

# Edit Version Event Cadence

## Conflict

Предыдущая модель создавала `EditVersionChangeSetPersisted` только при первом переходе `unchanged -> updated`. Новый discovery answer определяет событие как факт каждого успешно сохраненного content-changing draft state с непустым diff.

## Blocks

Без единой cadence audit/read-model subscribers не могут однозначно отличить новое persisted состояние от no-op save или idempotent retry.

## Resolution

`EditVersionChangeSetPersisted` возникает на каждый успешный content-changing save с непустым diff, включая `updated -> updated`. Revert к baseline создает отдельный `EditVersionChangeSetCleared`. No-op save и idempotent retry не создают событий.

## Consequences

- «Впервые стал dirty» остается derived signal из последовательности событий, а не единственным event boundary.
- `DraftVersionToken` меняется на content-changing save и revert, но не на no-op/retry.
- Current `operation` продолжает отражать diff относительно baseline, а не историю событий.
