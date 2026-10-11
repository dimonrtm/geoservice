---
title: Edit Version Save Request State Machine
type: state-machine
status: active
created: 2026-07-31
updated: 2026-10-12
source: "RAW_inputs/meetings/demo_utility_gis.md; docs/sprint_2/2026-10-12-save-recovery-rules-decision.md"
tags: [domain-knowledge, ddd, state-machine, edit-version, idempotency]
confidence: high
related: [Wiki/entities/edit_version, Wiki/value_objects/command_id, Wiki/value_objects/draft_version_token, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/aggregates/edit_version, DDD_Wiki/state_machines/edit_version_persisted_change_set]
---

# Edit Version Save Request State Machine

Состояние принадлежит operation, идентифицированной `CommandId`, и не заменяет lifecycle `EditVersion` или состояние persisted change set.

```text
NoCommittedRecord -- accepted in transaction --> Running (uncommitted)
Running -- commit successful outcome         --> Succeeded
Running -- commit ordinary domain rejection  --> Rejected
Running -- rollback                         --> previous committed state
Succeeded | Rejected -- matching retry       --> same terminal result
Rejected(access-retry allowed) -- explicit resume with current guards --> Running
any reserved state       -- same id, different fingerprint --> IdReuseRejected
any state after EditVersion closed             --> SaveContextClosed
```

## State Meaning

- `NoCommittedRecord`: нет committed записи данной команды; запрос мог ещё не прийти либо транзакция откатилась;
- `Running`: промежуточное состояние внутри транзакции; commit с оставшимся `running` запрещён;
- `Succeeded`: mutation выполнена не более одного раза, terminal result сохранён;
- `Rejected`: domain rejection сохранён; исправленный intent требует нового `CommandId`. Только предусмотренный access rejection допускает продолжение прежнего намерения после явного подтверждения и текущих guards; rollback возобновления восстанавливает прежний committed отказ;
- `IdReuseRejected`: тот же id предъявлен с другим fingerprint;
- `SaveContextClosed`: `EditVersion` уже posted/closed/cancelled/read-only/archived, старый request не становится новым намерением.

## Retention

Пользователь принял разграничение 2026-10-12. `OutcomePending` не является durable статусом серверной операции: потеря ответа оставляет неизвестным для редактора, произошёл ли commit. Это описывает [[DDD_Wiki/state_machines/editor_save_recovery]]. Конкурирующий retry сериализуется и проверяет committed результат; отдельный pending response/polling не вводится. Невозможность установить исход не является разрешением создать новое намерение автоматически. Replay подтверждает исходную операцию, актуальное состояние читается отдельно.

Операционный registry живёт весь lifecycle `EditVersion` и переживает reconnect, relogin и смену устройства. Append-only history save operations хранится отдельно по records policy `WorkOrder`/authoritative data; точный долгосрочный срок пока не определён.
