---
title: Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-10-18
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, ddd]
---

# Wiki

`Wiki/` хранит канонические атомарные доменные знания проекта: словарь, сущности, value objects, концепции, участников, внешние системы, команды, события, политики, спецификации, конфликты и вопросы.

## Реестры

Исследование восстановления редактора от 2026-10-11 добавило правила, принятые пользователем 2026-10-12: [[Wiki/glossary/editing_result_states]], [[Wiki/policies/editor_recovery_policy]], [[Wiki/policies/geometry_quality_escalation_policy]] и [[Wiki/policies/change_history_retention_policy]]. Это синтез позиции заказчика, не подтверждённое интервью. Разграничение состояния операции и осведомлённости редактора принято; конфликт разрешён: [[Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]].

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

## Решения условной организации 2026-10-13

[[RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions]] заменяет ожидание принятия прежних предложений: recovery, дефекты источника, evidence, основание правки и хранение приняты как правила модели. См. [[Wiki/policies/recovery_case_resolution_policy]], [[Wiki/policies/edit_change_justification_policy]], [[Wiki/policies/geometry_quality_escalation_policy]], [[Wiki/policies/positional_accuracy_acceptance_policy]], [[Wiki/policies/change_history_retention_policy]].

Новая [[Wiki/specifications/simulated_line_positional_acceptance]] задаёт SIM-UGIS-POS-001 v1.0 и аналитическое evidence. Она не подтверждает реальную точность L-003. Остались 2 вопроса сверки metadata/fixture; шесть организационных/модельных вопросов отвечены. [[Wiki/conflicts/2026-10-13-real-organization-vs-simulated-decisions]] resolved, реализация отдельно в FU-2026-10-13-004. Исторический RAW сохранён.

## Пограничные случаи восстановления 2026-10-16

[[RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research]] уточняет [[Wiki/policies/editor_recovery_policy]], [[Wiki/policies/recovery_case_resolution_policy]] и [[Wiki/glossary/editing_result_states]]. Новая [[Wiki/specifications/editing_resumption_allowed]] отделяет выяснение исхода, разрешение новой записи и закрытие разбора. Правила условной организации активны; реализация и проверка отдельно.

## Пригодность данных и доказательная оценка

[[RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research]] содержит 17 веб-источников и 15 ответов. Канонические правила: [[Wiki/policies/demo_dataset_qualification_policy]], [[Wiki/specifications/saved_line_quality_assessment]]. Числовые критерии сохранены; реализация и фактическая проверка данных не заявлены.

## Смысл правки инженерной сети — 2026-10-16

[[Wiki/glossary/network_edit_meaning]] и [[Wiki/policies/network_edit_semantics_policy]] различают исправление сведений, физическое изменение и оформление; 15 ответов [[RAW_inputs/research_results/2026-10-16-utility-gis-editor-network-semantics-research]] задают границы передачи без расширения реализации.

## Осознанная правка и новые предметные знания

- [[Wiki/concepts/field_observation_acceptance]] — область принятия свидетельства.
- [[Wiki/concepts/network_representation_and_operational_state]] — актив, отношения, состояние и расчёт.
- [[Wiki/policies/intentional_line_editing_policy]] — правила 15 ответов discovery.
- [[Wiki/specifications/line_edit_exercise_completed]] — граница доказательства упражнения.
