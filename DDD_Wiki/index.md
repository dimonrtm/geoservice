---
title: DDD Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-07-31
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

Текущие пробелы, противоречия и готовность к discovery фиксируются в [[DDD_Wiki/model_health]].

## Актуальный First-Save Срез

- [[DDD_Wiki/aggregates/edit_version]] - consistency boundary, baseline/current snapshots, token и idempotency.
- [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] - blocking spatial/structure guards, technical save с явным positional status, canonical single-vertex save.
- [[DDD_Wiki/state_machines/edit_version_persisted_change_set]] - `Unchanged` / `Updated`, save/revert/no-op/reject.
- [[DDD_Wiki/state_machines/edit_version_save_request]] - одна operation на `CommandId`, concurrent retry, terminal result и закрытый save context.
- [[DDD_Wiki/use_cases/utility_editor_workflow]] - end-to-end save/readback/revert proof.
