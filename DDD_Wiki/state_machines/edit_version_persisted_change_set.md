---
title: Edit Version Persisted Change Set State Machine
type: state-machine
status: planned
created: 2026-07-25
updated: 2026-07-31
source: "RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, ddd, state-machine, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/commands/update_edit_version_feature_geometry, Wiki/domain_events/edit_version_change_set_persisted, Wiki/domain_events/edit_version_change_set_cleared, DDD_Wiki/aggregates/edit_version, DDD_Wiki/state_machines/edit_version_save_request]
---

# Edit Version Persisted Change Set State Machine

Состояние описывает current diff относительно immutable [[Wiki/glossary/base_work_state]], а не lifecycle `EditVersion`. Сравнение выполняется после канонизации изменённой вершины к точности хранения координат.

```text
Unchanged -- save(valid non-empty diff) --> Updated
Updated   -- save(valid non-empty diff) --> Updated
Updated   -- save(result == baseline)   --> Unchanged
Unchanged -- save(no-op baseline)       --> Unchanged
Unchanged -- save(invalid or stale)     --> Rejected
Updated   -- save(invalid or stale)     --> Rejected
```

## State Meaning

- `Unchanged`: `operation=unchanged`, `hasPersistedChangeSet=false`.
- `Updated`: `operation=updated`, `hasPersistedChangeSet=true`, `topologyChecked=not_checked`.
- `Rejected`: не persisted state; aggregate остается в предыдущем `Unchanged` или `Updated`.

## Event And Token Rules

- Content-changing save с непустым diff меняет token и создает `EditVersionChangeSetPersisted`.
- Revert к baseline меняет token и создает `EditVersionChangeSetCleared`.
- No-op после coordinate normalization и idempotent retry не меняют token и не создают событие.
- Invalid geometry, prohibited diff и stale token отклоняются атомарно.
- Lifecycle и concurrent retry самой save operation описывает [[DDD_Wiki/state_machines/edit_version_save_request]]; terminal domain rejection не становится persisted change-set state.
