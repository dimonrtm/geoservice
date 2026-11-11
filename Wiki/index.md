---
title: Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-11-10
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, ddd]
---

# Wiki

## Текущее состояние

После сверки кода 2026-11-09 [[DDD_Wiki/model_health]] актуализирован, stale снят; FU-2026-10-11-001 resolved. First-save/API/UI/recovery реализованы; 105 выбранных frontend-тестов проходят. [Матрица реализации](../docs/verification/2026-11-09-model-health-code-reconciliation.md) отделяет их от ещё не реализованных evaluator/review/post/withdrawal/correction. Открытых follow-up’ов 18; после ingest 10.11.2026 открытых вопросов нет; три вопроса о зависимостях нарядов answered в [[Wiki/_registry/questions]]; канонических конфликтов 0, legacy-конфликтов 1. Все 60 RAW обработаны. Metadata/fixture подтверждены протоколом 08.11 для revision 49, позиционная точность не подтверждена. Приняты условия зависимости, её пересмотра и разбора взаимного ожидания; технический остаток ведётся отдельно. Датированные записи ниже исторические.

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

## Применимость основания сохранённой правки

[[Wiki/concepts/change_basis_lifecycle]] и [[Wiki/concepts/evidence_dependency]] описывают новые знания корпуса 77 документов. [[Wiki/policies/change_basis_revision_policy]] и [[Wiki/specifications/line_edit_basis_applicable]] задают принятые правила условной организации при изменении задания, редакции или отзыве источника. Ручная карточка достаточна до отдельной реализации; positional status и текущий scope сохраняются.

## Применимость заключения — 2026-10-22

[[Wiki/concepts/assessment_statement_lifecycle]] и [[Wiki/concepts/assessment_delivery_and_acceptance]] описывают выпуск, область, редакции и передачу. [[Wiki/policies/assessment_issue_and_correction_policy]] закрепляет 15 ответов; [[Wiki/specifications/assessment_statement_usable]] проверяет пригодность конкретного утверждения для цели. Корпус 84 внешних документа, источники и ограничения находятся в RAW. Это модель ручной процедуры, без расширения Save и позиционного критерия.

## Допуск экземпляра учебных данных — 2026-11-07

Корпус 80 документов и 15 ответов уточняет [[Wiki/policies/demo_dataset_qualification_policy]]. Новые понятия: [[Wiki/concepts/dataset_instance_and_record_identity]], [[Wiki/concepts/coordinate_operation_provenance]]. Критерий ручного допуска — [[Wiki/specifications/demo_dataset_instance_qualified]]. Правила приняты условной организацией; два фактических вопроса metadata/fixture не закрыты.

## Метод и охват квалификации — 2026-11-08

[[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-research]] уточняет существующие [[Wiki/concepts/field_observation_acceptance]], [[Wiki/concepts/assessment_statement_lifecycle]], [[Wiki/concepts/dataset_instance_and_record_identity]] и [[Wiki/concepts/assessment_delivery_and_acceptance]]. На общем корпусе 78 документов приняты 15 ответов [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers]]; обновлены [[Wiki/policies/demo_dataset_qualification_policy]] и [[Wiki/specifications/demo_dataset_instance_qualified]]. Фактическая БД не проверена.

## Представления и доказательства — 2026-11-08

[[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-research]] — 80 внешних документов, 26 новых нормализованных ссылок. Уточнения: [[Wiki/concepts/network_representation_and_operational_state]], [[Wiki/concepts/dataset_instance_and_record_identity]], [[Wiki/concepts/assessment_statement_lifecycle]]. [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-answers]] — 15 ответов и ручные критерии; фактические metadata/fixture не подтверждены.

## Отзыв и коррекция публикации — 2026-11-09

[[Wiki/concepts/published_result_correction_case]], [[Wiki/policies/review_package_withdrawal_policy]], [[Wiki/policies/published_result_correction_policy]] и [[Wiki/specifications/published_result_correction_closed]] фиксируют новый прирост модели. [[Wiki/specifications/post_allowed]] уточнён. Два ответа условной организации отделены от фактов источников и реализации.

## Зависимые наряды — 2026-11-10

75 документов, 25 новых нормализованных URL; три ответа условной организации, без runtime-приёмки. [[Wiki/concepts/work_result_dependency]], [[Wiki/policies/dependent_work_coordination_policy]], [[Wiki/specifications/dependent_work_step_allowed]], [[DDD_Wiki/use_cases/coordinate_dependent_work_orders]]. Источники: [[Vision_wiki/chats/2026-11-10-dependencies-research]], [[Vision_wiki/chats/2026-11-10-dependencies-answers]].
