---
title: Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-07-31
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, ddd]
---

# Wiki

`Wiki/` хранит канонические атомарные доменные знания проекта: словарь, сущности, value objects, концепции, участников, внешние системы, команды, события, политики, спецификации, конфликты и вопросы.

## Реестры

- [[Wiki/_registry/glossary]]
- [[Wiki/_registry/entities]]
- [[Wiki/_registry/value_objects]]
- [[Wiki/_registry/concepts]]
- [[Wiki/_registry/actors]]
- [[Wiki/_registry/external_systems]]
- [[Wiki/_registry/commands]]
- [[Wiki/_registry/domain_events]]
- [[Wiki/_registry/system_events]]
- [[Wiki/_registry/policies]]
- [[Wiki/_registry/specifications]]
- [[Wiki/_registry/conflicts]]
- [[Wiki/_registry/questions]]

## Каталоги

- `Wiki/glossary/` - термины единого доменного языка.
- `Wiki/entities/` - сущности с устойчивой идентичностью.
- `Wiki/value_objects/` - неизменяемые значения, равенство которых определяется структурой.
- `Wiki/concepts/` - доменные понятия, которые пока не стали сущностью, value object или политикой.
- `Wiki/actors/` - пользователи, роли и внешние участники процесса.
- `Wiki/external_systems/` - внешние системы и антикоррупционные границы.
- `Wiki/commands/` - намерения изменить состояние модели.
- `Wiki/domain_events/` - значимые факты домена, произошедшие в прошлом.
- `Wiki/system_events/` - технические события системы и интеграций.
- `Wiki/policies/` - правила принятия решений.
- `Wiki/specifications/` - проверяемые предикаты доменной модели.
- `Wiki/conflicts/` - противоречия, блокирующие непротиворечивую модель.
- `Wiki/questions/` - вопросы discovery и планирования спринтов.

## Правила Поддержки

Каждый содержательный узел `Wiki/` должен иметь `source`, `confidence` и `related`. Если новый raw-файл уточняет модель, `/ingest` обновляет соответствующие узлы и реестры, а конфликтные знания фиксирует в `Wiki/conflicts/`.

## Актуальный First-Save Контракт

- [[Wiki/glossary/positional_accuracy_for_acceptance]], [[Wiki/glossary/coordinate_storage_precision]] и [[Wiki/glossary/base_work_state]] - подтверждённый ubiquitous language для точности и baseline.
- [[Wiki/policies/edit_geometry_precision_policy]] - server-side канонизация только изменённой вершины по metadata dataset, no-op и atomic reject.
- [[Wiki/policies/positional_accuracy_acceptance_policy]] - technical save с явным positional status и обязательная verified acceptance до review/post.
- [[Wiki/commands/update_edit_version_feature_geometry]] - full resulting geometry с guard «одна line feature / одна внутренняя вершина».
- [[Wiki/value_objects/draft_version_token]] и [[Wiki/value_objects/command_id]] - optimistic concurrency отдельно от lifecycle-safe idempotent operation.
- [[Wiki/domain_events/edit_version_change_set_persisted]] и [[Wiki/domain_events/edit_version_change_set_cleared]] - события save/revert.
- [[Wiki/specifications/edit_version_basic_draft_validation]] - atomic hard guards и `topologyChecked=not_checked`.
