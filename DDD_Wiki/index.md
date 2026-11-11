---
title: DDD Wiki
type: index
status: active
created: 2026-06-24
updated: 2026-11-10
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, ddd]
---

# DDD Wiki

## Текущее состояние

После сверки кода 2026-11-09 [[DDD_Wiki/model_health]] актуализирован, stale снят; FU-2026-10-11-001 resolved. First-save/API/UI/recovery реализованы; 105 выбранных frontend-тестов проходят. [Матрица реализации](../docs/verification/2026-11-09-model-health-code-reconciliation.md) отделяет их от ещё не реализованных evaluator/review/post/withdrawal/correction. Открытых follow-up’ов 18; после ingest 10.11.2026 открытых вопросов нет; три вопроса о зависимостях нарядов answered в [[Wiki/_registry/questions]]; канонических конфликтов 0, legacy-конфликтов 1. Все 60 RAW обработаны. Metadata/fixture подтверждены протоколом 08.11 для revision 49, позиционная точность не подтверждена. Приняты условия зависимости, её пересмотра и разбора взаимного ожидания; технический остаток ведётся отдельно. Датированные записи ниже исторические.

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

Сверка 2026-11-07: [Отчёт S2-X01](../docs/sprint_2/2026-10-23-s2-x01-recovery-implementation-report.md) фиксирует завершение реализации и проверок 2026-10-23: IndexedDB recovery, возврат доступа, независимые наряды и сравнение отклонённой попытки. При `/sync-vision` runtime-проверки повторно не выполнялись. Автоматический перенос candidate, evaluator и восстановление уничтоженного storage не входят в этот результат. Доменная очередь и два вопроса metadata/fixture остаются на сверке; [[DDD_Wiki/model_health]] сохраняет `stale`. Актуальное техническое чтение карты, ChangeSet и baseline — [[Code_wiki/архитектура/edit_version_api_readback]].

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

## Переоценка основания

[[DDD_Wiki/use_cases/reassess_line_edit_basis]] дополняет подготовку/оценку линии: revision источника, зависимости свидетельств, неизвестное время, новая причина и передача разбора. Границы WorkOrder/EditVersion и события не изменены; внешнее основание и geometry Save не образуют одну транзакцию.

## Выпуск и исправление оценки линии

[[DDD_Wiki/use_cases/issue_and_correct_line_assessment]] продолжает оценку сохранённой линии: исторический вывод, частичный охват, спор, пересмотр, уведомление и явная применимость. Новых aggregate, команд и API нет; реализация остаётся отдельной задачей.

## Квалификация экземпляра — 2026-11-07

[[DDD_Wiki/use_cases/prepare_and_check_line_edit]] уточнён через [[Wiki/specifications/demo_dataset_instance_qualified]]: экземпляр/запись, происхождение координат, persisted policy, структура/AOI, ветка упражнения и согласованность свидетельств. Новые aggregate, команды, события и транзакционные границы не вводятся. Runtime metadata/fixture остаются на сверке.

## Метод и охват проверки — 2026-11-08

[[DDD_Wiki/use_cases/prepare_and_check_line_edit]] уточнён по [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers]]: свойство, метод, состояние и область проверки фиксируются в ручной карточке. 78 документов — общий корпус анализа и ответов. Новых aggregate, событий и транзакций нет.

## Уточнение представлений — 2026-11-08

[[DDD_Wiki/use_cases/prepare_and_check_line_edit]] дополнен по [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-answers]]: назначение геометрии, идентичность после обмена и ограничение вывода охватом данных. Существующие агрегаты и инварианты сохранены; metadata/fixture остаются открытыми.

## Исключения публикационного цикла — 2026-11-09

[[DDD_Wiki/use_cases/withdraw_review_package]] и [[DDD_Wiki/use_cases/correct_published_result]] дополняют ReviewPackage и WorkOrder lifecycle: терминальный отзыв до допуска post, выяснение допущенного outcome, новый связанный исправительный цикл и документальная ветка. Новых aggregate, API и Save enum нет; история и последующие законные изменения сохраняются.

## Зависимые наряды — 2026-11-10

75 документов, 25 новых нормализованных URL; три ответа условной организации, без runtime-приёмки. [[Wiki/concepts/work_result_dependency]], [[Wiki/policies/dependent_work_coordination_policy]], [[Wiki/specifications/dependent_work_step_allowed]], [[DDD_Wiki/use_cases/coordinate_dependent_work_orders]]. Источники: [[Vision_wiki/chats/2026-11-10-dependencies-research]], [[Vision_wiki/chats/2026-11-10-dependencies-answers]].
