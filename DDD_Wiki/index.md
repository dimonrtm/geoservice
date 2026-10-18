---
title: DDD Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-10-18
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, ddd]
---

# DDD Wiki

`DDD_Wiki/` хранит доменную модель в терминах Domain-Driven Design: домен, поддомены, bounded contexts, context map, aggregates, state machines, invariants, use cases и integration patterns.

## Разделы

- `DDD_Wiki/domains/` - область бизнеса целиком.
- `DDD_Wiki/subdomains/` - core, supporting и generic subdomains.
- `DDD_Wiki/bounded_contexts/` - границы языка и модели.
- `DDD_Wiki/context_map/` - отношения контекстов и интеграционные паттерны.
- `DDD_Wiki/aggregates/` - агрегаты, корни агрегатов и инварианты транзакционной согласованности.
- `DDD_Wiki/state_machines/` - жизненные циклы ключевых сущностей.
- `DDD_Wiki/invariants/` - правила, которые модель обязана сохранять.
- `DDD_Wiki/use_cases/` - сценарии, связывающие команды, события и политики.
- `DDD_Wiki/integration_patterns/` - ACL, published language, open host service и другие интеграционные решения DDD.

## Здоровье Модели

[[DDD_Wiki/state_machines/editor_save_recovery]] — принятая 2026-10-12 модель осведомлённости редактора и восстановления. Не заменяет состояние серверной операции; разграничение принято по [[Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]].

Текущие пробелы, противоречия и готовность к discovery фиксируются в [[DDD_Wiki/model_health]].

## Актуальный First-Save Срез

- [[DDD_Wiki/aggregates/edit_version]] - consistency boundary, baseline/current snapshots, token и idempotency.
- [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] - blocking spatial/structure guards, technical save с явным positional status, canonical single-vertex save.
- [[DDD_Wiki/state_machines/edit_version_persisted_change_set]] - `Unchanged` / `Updated`, save/revert/no-op/reject.
- [[DDD_Wiki/state_machines/edit_version_save_request]] - одна operation на `CommandId`, concurrent retry, terminal result и закрытый save context.
- [[DDD_Wiki/use_cases/utility_editor_workflow]] - end-to-end save/readback/revert proof.

## Восстановление прерванной работы в условной организации

[[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] активно как принятое правило модели: обязанности агента, эскалация, доказательство исхода/current и возобновление без изменения baseline. Новые серверные состояния, роли доступа и restart не считаются реализованными. [[Wiki/specifications/simulated_line_positional_acceptance]] задаёт учебный критерий, но не снимает review/post guards. Реализация — FU-2026-10-13-004.

## Уточнения восстановления 2026-10-16

[[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] и [[DDD_Wiki/state_machines/editor_save_recovery]] учитывают позднее подтверждение, закрытый контекст, смену доступа и актуальность согласия на Revert. [[Wiki/specifications/editing_resumption_allowed]] не вводит новых серверных состояний, aggregates или access roles.

## Оценка качества сохранённой правки

[[DDD_Wiki/use_cases/assess_saved_line_quality]] связывает пригодность данных, сохранённое состояние и доказательное заключение. Активность сценария означает принятие правил условной организации, не готовность evaluator.

## Предметная интерпретация правки

[[DDD_Wiki/use_cases/utility_editor_workflow]] дополнен по [[Wiki/policies/network_edit_semantics_policy]]: идентичность и намерение до правки, область доказательства и ограничения при передаче. Сетевые расчёты остаются самостоятельными сценариями.

- [[DDD_Wiki/use_cases/prepare_and_check_line_edit]] — подготовка и доказательство осознанной правки линии.
