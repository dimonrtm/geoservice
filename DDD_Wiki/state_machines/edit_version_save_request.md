---
title: Edit Version Save Request State Machine
type: state-machine
status: planned
created: 2026-07-31
updated: 2026-07-31
source: RAW_inputs/meetings/demo_utility_gis.md
tags: [domain-knowledge, ddd, state-machine, edit-version, idempotency]
confidence: high
related: [Wiki/entities/edit_version, Wiki/value_objects/command_id, Wiki/value_objects/draft_version_token, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/aggregates/edit_version, DDD_Wiki/state_machines/edit_version_persisted_change_set]
---

# Edit Version Save Request State Machine

Состояние принадлежит operation, идентифицированной `CommandId`, и не заменяет lifecycle `EditVersion` или состояние persisted change set.

```text
NotReceived -- accepted(same id + fingerprint) --> Running
Running     -- commit succeeds                --> Succeeded
Running     -- domain guard rejects           --> Rejected
Running     -- outcome unknown after commit   --> OutcomePending
OutcomePending -- outcome established         --> Succeeded | Rejected

Running | OutcomePending -- retry(same fingerprint) --> same operation/status
Succeeded | Rejected     -- retry(same fingerprint) --> same terminal result
any reserved state       -- same id, different fingerprint --> IdReuseRejected
any state after EditVersion closed             --> SaveContextClosed
```

## State Meaning

- `NotReceived`: request не был принят или распознан, `CommandId` не зарезервирован;
- `Running`: существует ровно одна выполняемая operation;
- `OutcomePending`: commit мог начаться, поэтому id зарезервирован до установления результата;
- `Succeeded`: mutation выполнена не более одного раза, terminal result сохранён;
- `Rejected`: domain rejection сохранён как terminal result; исправленный intent требует нового `CommandId`;
- `IdReuseRejected`: тот же id предъявлен с другим fingerprint;
- `SaveContextClosed`: `EditVersion` уже posted/closed/cancelled/read-only/archived, старый request не становится новым намерением.

## Retention

Операционный registry живёт весь lifecycle `EditVersion` и переживает reconnect, relogin и смену устройства. Append-only history save operations хранится отдельно по records policy `WorkOrder`/authoritative data; точный долгосрочный срок пока не определён.
