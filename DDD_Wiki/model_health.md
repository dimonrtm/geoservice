---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-11-26
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md; RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research.md; RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research.md; RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-answers.md; RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-answers.md; RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers.md; docs/verification/2026-11-09-model-health-code-reconciliation.md"
tags: [domain-knowledge, ddd, health]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Состояние модели на 26.11.2026

Разбор 18 исследовательских кандидатов дал девять самостоятельных сценариев и три варианта. Два кандидата отложены, четыре отнесены к смежным службам. Это решение условной организации о составе доменной модели. Очередь реализации определяется отдельно. [Каталог из 22 сценариев](use_cases/_info.md) · [Основания решений](use_cases/candidates/_info.md).

Сверка реализации от 09.11.2026 — [матрица и проверки](../docs/verification/2026-11-09-model-health-code-reconciliation.md). First-save, публичные Save/Revert/readback и S2-X01 recovery реализованы; 105 выбранных frontend-тестов прошли. Метка stale снята как признак устранённого отставания этого документа. Backend/PostGIS/M4 и БД повторно не проверялись; прежние протоколы сохраняют свою область.

В реестре 79 отвеченных вопросов. По повторному исследованию работы редактора приняты проверка разнесения путей и контроль серии обработанных изменений. [[RAW_inputs/documents/2026-11-26-editor-practice-analysis#Решения по целям участников]]. Оба решения по волокнам от 26 ноября приняты. [[RAW_inputs/documents/2026-11-26-field-evidence-answers]]. Все 15 вопросов от 24 ноября закрыты решениями условной организации. [[Wiki/_registry/questions#Обзор всей доменной модели — 24 ноября]]. Все 15 вопросов обзора от 21 ноября получили ответы по [[RAW_inputs/research_results/2026-11-22-utility-gis-editor-governance-answers]]. Путь от обследования до выпуска описан в [[DDD_Wiki/use_cases/reconcile_field_and_inventory_records]]. Три решения об учёте активов и предмете наряда приняты условной организацией по [[RAW_inputs/research_results/2026-11-21-utility-gis-editor-asset-lifecycle-answers]]. Активных канонических конфликтов нет, в Vision остаётся один конфликт о старом Release 1. В [[Vision_wiki/decisions/followups/index]] открыты 20 пунктов. FU-2026-11-21-001 охватывает документацию реализации, FU-2026-11-21-002 — устаревший статус в карте контекстов. Сверка first-save по FU-2026-10-11-001 завершена. Реализация остальных принятых правил, включая координацию зависимых нарядов, остаётся в FU-2026-10-13-004. Датированные сводки ниже исторические.

В редакции роли от 22.11.2026 приняты четыре уточнения сквозного сценария. Для каждого приведён пример с ожидаемым исходом. Решения приняты условной организацией, статус реализации ведётся в очереди спринта. [[RAW_inputs/documents/UtilityGisEditorRole#Прирост модели]], [[DDD_Wiki/use_cases/reconcile_field_and_inventory_records]].

24.11.2026 по 97 рассказам практиков уточнены происхождение возвращённых полей, завершение узкой проверки при открытом расследовании и допустимая выдача смене, если её карта отстаёт. [[RAW_inputs/documents/UtilityGisEditorRole#Что изменилось в понимании работы редактора]], [[DDD_Wiki/use_cases/utility_editor_workflow#Когда следующий шаг выполняет другая смена]].

24.11.2026 в действующих сценариях уточнены условия пересъёмки, применимость сводки при выборочном обследовании и подтверждение длины пути по графу. Разбор касается доменных правил. Статус реализации опирается на ранее указанную сверку. [[DDD_Wiki/use_cases/reconcile_field_and_inventory_records#Что делать с результатом проверки отчёта]], [[DDD_Wiki/use_cases/utility_editor_workflow#Основание полевой правки и границы проверки]].

## История discovery до сверки кода — 2026-11-09

DISC-2026-11-09-01/02 answered по [[RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers]], общий корпус — 88 документов. Приняты отзыв до допуска post и новый связанный цикл коррекции. Обработаны оба новых RAW; всего 58. Открытых вопросов 0, follow-up’ов 19, активных канонических конфликтов 0, legacy-конфликтов 1. Stale сохраняется из-за сверки реализации; исследование не является runtime-приёмкой.

## Синхронизация до discovery — 2026-11-09

Все 56 RAW индексированы как обработанные, новых необработанных нет. Реестры Wiki покрывают существующие ноды. Открыты 19 follow-up’ов, вопросов — 0; активных канонических конфликтов — 0, legacy-конфликтов — 1. Единственная stale-нода — этот документ: техническая очередь требует отдельной сверки с реализацией. Lint: 37 известных missing_frontmatter только в RAW. Активная discovery-таблица ниже согласована с реестром и следующим действием [[memory/project-state]]; закрытая проверка L-003 вынесена из таблицы с основанием. Runtime-проверки при синхронизации не повторялись.

## Фактическая сверка metadata/fixture — 2026-11-08

[Протокол](../docs/verification/2026-11-08-demo-dataset-runtime-check.md) подтверждает локальную L-003 и persisted policy версии revision 49. Два вопроса metadata/fixture отвечены; текущий счёт открытых вопросов — 0. 19 follow-up сохраняются: FU-2026-10-11-001 требует сверки остальной доменной очереди. Метка stale остаётся по этой причине. Нижеследующие исследования описывают состояние до runtime-проверки и не отменяют её результат.

## Исторический срез после ingest, до runtime-проверки — 2026-11-08

Обработаны два RAW-артефакта исследования представлений с общим корпусом 80 внешних документов: анализ и 15 ответов. Всего RAW — 56, все индексированы обработанными. 19 follow-up’ов, два metadata/fixture вопроса, 0 активных канонических конфликтов и 1 legacy-конфликт сохраняются.

[[Wiki/specifications/demo_dataset_instance_qualified]] конкретизирует допуск экземпляра; [[DDD_Wiki/use_cases/prepare_and_check_line_edit]] включает сверку идентичности, происхождения координат, persisted policy и структуры/AOI. Это принятые ручные правила, не реализованный endpoint/evaluator. Уточнение 08.11 добавляет явные свойство, метод, состояние и фактический охват проверки, различает непроверенность и установленное несоответствие; источник — [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers]].

FU-2026-10-11-001 сохраняет расхождение между ожидаемым происхождением metadata и конфигурационным default, а также фактическую сверку L-003 старого volume. Фактическая БД не опрашивалась. Метка stale остаётся для этой сверки и доменной очереди. Датированные сводки ниже исторические.

## История сверок состояния

Сверка `/sync-vision` 2026-11-08: 54 RAW-источника, все отмечены обработанными; новых необработанных нет. Открыты 19 follow-up’ов и 2 вопроса metadata/fixture. Активных канонических конфликтов — 0, legacy-конфликтов — 1. Все реестры `Wiki/_registry` покрывают существующие ноды. Lint: 37 известных `missing_frontmatter` только в RAW. Единственная stale-нода — `DDD_Wiki/model_health`; метка сохраняется до сверки очереди реализации и metadata/fixture по FU-2026-10-11-001.

[Отчёт S2-X01](../docs/sprint_2/2026-10-23-s2-x01-recovery-implementation-report.md) фиксирует завершение реализации и проверок 2026-10-23: IndexedDB recovery, возврат доступа, независимые наряды и сравнение отклонённой попытки. При `/sync-vision` runtime-проверки повторно не выполнялись. Автоматический перенос candidate, evaluator и восстановление уничтоженного storage не входят в этот результат. Технические источники — [[Code_wiki/архитектура/frontend_save_recovery]], [[Code_wiki/архитектура/browser_auth_sessions]] и [[Code_wiki/архитектура/edit_version_api_readback]]. Прежние ожидания S2-X01 ниже исторические; доменные follow-up’ы не закрываются.

Сверка `/sync-vision` 2026-10-22: все 48 RAW обработаны, новых необработанных нет; 19 открытых follow-up’ов, 2 вопроса metadata/fixture, 0 активных канонических конфликтов и 1 активный legacy-конфликт. Реестры `Wiki/_registry` покрывают существующие ноды. Lint: 37 известных `missing_frontmatter` только в RAW. Единственная нода с меткой `stale` — этот документ; метка сохраняется для очереди реализации и metadata/fixture по `FU-2026-10-11-001`.

[[Code_wiki/архитектура/frontend_save_recovery]] в редакции 2026-10-21 подтверждает подключение Save/Revert controls и ручных retry/readback. [Отчёт M4](../docs/sprint_2/2026-10-21-day-12-m4-report.md) фиксирует два успешных сценария потери ответа после commit, restart API, refresh, replay и GET для Save/Revert. Это свидетельство указанного прогона, не повторная runtime-проверка при синхронизации. S2-X01, evaluator и организационные правила не считаются завершёнными; вопросы и конфликты не закрываются. Датированные утверждения ниже об отсутствии UI или проверок следует читать как исторические срезы.

Сверка `/sync-vision` 2026-10-19: 19 открытых follow-up’ов, 2 вопроса metadata/fixture, 0 активных канонических конфликтов; один legacy-конфликт остаётся active. После ingest двух новых исследований 2026-10-19 учтены и обработаны все 48 RAW-источников; новых необработанных нет. Технические основания Save/recovery и fixture доступны в [[Code_wiki/архитектура/edit_version_save_orchestration]], [[Code_wiki/архитектура/frontend_save_recovery]] и [[Code_wiki/архитектура/edit_geometry_fixture_metadata]]. Единственная stale-нода — этот документ: очередь реализации и metadata/fixture требуют сверки по `FU-2026-10-11-001`. Статусы вопросов и конфликтов не изменены; новые правила модели не означают runtime-приёмку. Lint: 37 известных `missing_frontmatter` только в RAW.

Сверка `/sync-vision` 2026-10-16: [[Wiki/_registry/questions]] содержит 2 открытых вопроса metadata/fixture, [[Vision_wiki/decisions/followups/index]] — 19 открытых follow-up’ов; активных канонических blocking conflicts нет. Решения условной организации от 2026-10-13 приняты, [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] active. SIM-UGIS-POS-001 и SIM-UGIS-RET-001 определяют учебную приёмку и хранение, но не доказывают реализацию или точность L-003. Требования реальных сотрудников, интервью и внутренних документов не являются блокерами. Метка `stale` сохранена до сверки реализации по `FU-2026-10-11-001`; применение новых правил — `FU-2026-10-13-004`.

Датированные проверки и research-сводки ниже сохранены как исторический контекст; прежние числа вопросов и ожидания организационных входов заменены текущей сводкой и разделом «Текущее уточнение». Очередь спринтов требует отдельной сверки с кодом и не подтверждает отсутствие уже реализованных частей.

Проверка `/sync-vision` от 2026-10-11: доменные контракты ниже сохранены, но очередь реализации и утверждение о неподтверждённой fixture отстают от code reality. В `apps/backend/seeds/tests/test_seed_utility_dataset_specs.py` уже определена eligible line `L-003`, а `EditVersionService.save_geometry` реализует внутренний backend Save/Revert. Источники для сверки: [[Code_wiki/архитектура/edit_geometry_determinism]], [[Code_wiki/архитектура/edit_version_persistence]] и [артефакты Sprint 2](../docs/sprint_2/README.md). Это не подтверждает готовность публичного API/UI или positional acceptance.

После принятия правил 2026-10-12 активных blocking conflicts нет; реестр содержит 5 открытых вопросов. Вопросы о fixture и metadata требуют сверки с принятыми sprint-спецификациями до следующего discovery; автоматически они не закрыты. Сверка зарегистрирована как `FU-2026-10-11-001` в [[Vision_wiki/decisions/followups/index]].

Проверка `/sync-vision` от 2026-10-13: [[Code_wiki/архитектура/edit_version_api_readback]] фиксирует публичный Save API и согласованный workspace readback по ingest от 2026-10-12. Указанное выше ограничение по публичному API уточнено этим источником; готовность frontend и S2-X01 не подтверждена. Сохраняются 5 открытых вопросов и 0 активных blocking conflicts. Метка `stale` остаётся из-за очереди fixture/metadata и реализации ниже; содержательная сверка выполняется отдельно по `FU-2026-10-11-001`.

## Исследование Восстановления 2026-10-11

Источник: [[RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research]]. Ответы на 15 вопросов синтезированы от лица заказчика по девяти первичным источникам; это не интервью и не утверждённые организационные правила. Новые [[Wiki/glossary/editing_result_states]], [[Wiki/policies/editor_recovery_policy]], [[Wiki/policies/geometry_quality_escalation_policy]], [[Wiki/policies/change_history_retention_policy]] и [[DDD_Wiki/state_machines/editor_save_recovery]] приняты пользователем 2026-10-12 и имеют `active` (принятие правил, не доказательство реализации).

Политика восстановления и разграничение operation/observer приняты; D5-Q1 стало правилом текущего XY-среза. Реальный ответственный за исходные дефекты ещё не назначен. Недостающая реализация оформлена в [S2-X01](../docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md) вне календарных дней. Конкретная positional specification и срок history не получены. Этот ingest не подтверждает готовность публичного API/UI и не исправляет остальное отставание model health от реализации; метка `stale` сохранена.

## Дополнение представлений после ingest — 2026-11-08

Источник: [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-answers]]. Уточнены назначение геометрии, роли идентификаторов и знаменатель полноты. Существующие инварианты и агрегаты сохранены; 56 RAW обработаны. Новых конфликтов нет; metadata/fixture не проверены, stale сохраняется.

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, review/post и audit. Discovery answers закрыли поведение first-save contract; фактические metadata и fixture подтверждены протоколом 08.11.2026 для локальной revision 49. Контракт среза задаёт путь workspace -> `UpdateEditVersionFeatureGeometry` -> сдвиг ровно одной внутренней вершины одной существующей line feature -> server-side canonicalization по metadata dataset -> atomic save full resulting snapshot относительно единого базового состояния работы -> command response + persisted readback -> revert к baseline. Line должна быть valid/simple и `covered by` AOI; endpoints, structure, attributes и associations заморожены. Позиционная точность для приёмки берётся из утверждённой спецификации и evidence, coordinate grid — из spatial-reference metadata dataset; это разные правила. `POSITIONAL_ACCURACY_UNVERIFIED` разрешает technical save, но блокирует review/completion/post. `DraftVersionToken` защищает весь aggregate, а `CommandId` идентифицирует одну operation на весь lifecycle `EditVersion`, включая concurrent retry и повтор terminal rejection. `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff и хранит line identity + before/after + actor/time/baseline/command evidence; `EditVersionChangeSetCleared` возникает на revert; no-op/retry событий не создают. First-save readiness называется `persisted-draft-ready`: lifecycle остается `open`, topology - `not_checked`, review/post остается downstream context.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет активных blocking conflicts | - | clear | Реализовать/проверить оставшиеся правила по FU-2026-10-13-004; сверка документации FU-2026-10-11-001 завершена |

Разрешён 2026-10-12: [[Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]] по [решению пользователя](../docs/sprint_2/2026-10-12-save-recovery-rules-decision.md).

## Recently Resolved Conflicts

| Conflict | Resolution Source | Result |
| --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` | `Publisher` отделен от `Reviewer`; developer demo использует system `post-gate` для simulated technical post после computed `can_post`. |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/increment_after_open_workspace.md` | Review/post remains required downstream scope, но ближайший code slice сначала закрывает persisted edit change set. |
| [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; user chat 2026-06-26 | Новый contract отдельный и integrated; старый Release 2 artifact остается legacy/reference. |
| [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] | `RAW_inputs/meetings/increment_after_open_workspace.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` | Ближайший sprint начинается с persisted geometry diff existing line feature и edit-save-readback; `ReviewPackage`, `can_post`, simulated post, full audit, trace/subnetwork evidence, risk tiers, reviewer queue, endpoint rewiring и association mutation откладываются. |
| [[Wiki/conflicts/2026-07-25-edit-version-event-cadence]] | `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md` | `EditVersionChangeSetPersisted` эмитится на каждый content-changing save с непустым diff; revert создает `EditVersionChangeSetCleared`; no-op/retry событий не создают. |

## Current Coverage

Статус active в таблице означает принятую доменную модель. Реализация подтверждена отдельно матрицей выше: ReviewPackage/Review Post и positional evaluation ещё не реализованы.

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | active | [[Wiki/glossary/utility_gis_editing]], [[Wiki/glossary/positional_accuracy_for_acceptance]], [[Wiki/glossary/coordinate_storage_precision]] и [[Wiki/glossary/base_work_state]] закрепляют язык workflow, точности и baseline. |
| Subdomains | active | Core subdomain [[DDD_Wiki/subdomains/utility_authoritative_editing]] отделен от generic map editing. |
| Bounded Contexts | active | Выделены контексты Work Order, Utility Network, Review Post, Audit и Auth. |
| Context Map | active | [[DDD_Wiki/context_map/geoservice_context_map]] описывает upstream/downstream и границу application layer. |
| Aggregates | active | `WorkOrder`, `EditVersion` и `ReviewPackage` активны в доменной модели. |
| Commands And Events | active | `OpenEditVersion` активна; first write command - `UpdateEditVersionFeatureGeometry`; события `EditVersionChangeSetPersisted` и `EditVersionChangeSetCleared` описывают save/revert, `CommandId` отделяет retry от concurrency. |
| Policies And Specifications | active | Проверка назначения, [[Wiki/policies/edit_geometry_precision_policy]], [[Wiki/policies/positional_accuracy_acceptance_policy]], persisted change set, basic draft validation, ready-for-review, post allowed, review/post и stale policies активны. |
| Sprint Planning Inputs | active | Решения об идентичности активов входят в доменную модель. Техническая очередь ведётся отдельно в Current Sprint Planning Queue. |

## Current Discovery Queue

Открытых вопросов нет. Для DISC-2026-11-26-03 принято правило проверки двух путей по запрошенному уровню, дате и охвату. Разные каналы в общем коллекторе дают разные выводы по каналам и по сооружениям. [[RAW_inputs/documents/2026-11-26-editor-practice-answers#DISC-2026-11-26-03]] · [[Wiki/_registry/questions#Раздельная прокладка основного и резервного кабелей — 26 ноября]].

Для DISC-2026-11-26-01 принят порядок исправления подробной ведомости, для DISC-2026-11-26-02 — отдельная проверка снятия доказанно ложной пары при неизвестном продолжении. [[RAW_inputs/documents/2026-11-26-field-evidence-answers]] · [[Wiki/_registry/questions#Исправление записи о соединении волокон — 26 ноября]].

DISC-2026-11-24-01…15 отвечены. Решения и различающие примеры приведены в [[RAW_inputs/documents/2026-11-24-field-records-answers]], гипотезы об эффекте правил — в [[RAW_inputs/documents/2026-11-24-field-records-analysis]]. [[Wiki/_registry/questions#Обзор всей доменной модели — 24 ноября]].

DISC-2026-11-21-01/02/03 отвечены. Приняты правила периодов установки экземпляра, происхождения обслуживаемых участков и определения предмета открытого наряда. [[RAW_inputs/research_results/2026-11-21-utility-gis-editor-asset-lifecycle-answers]], [[DDD_Wiki/use_cases/record_physical_asset_change]]. Ответы о взаимозависимых нарядах — [[RAW_inputs/research_results/2026-11-10-utility-gis-editor-dependencies-answers]].

Сверка кода по FU-2026-11-21-001 и редакционная задача по карте контекстов FU-2026-11-21-002 ведутся отдельно. Инварианты текущего first-save — [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]].

## Current Sprint Planning Queue

**Приоритет от 24.11.2026 — полностью редактировать сеть в рабочей версии наряда.** До перехода к анализу путей, review и публикации редактор должен уметь изменять состав сети, геометрию, свойства и реальные записи соединений. Здесь зафиксирован порядок будущей работы. [Очередь с критериями приёмки](../docs/planning/network-editor-backlog.md) · [Целевая модель данных](aggregates/edit_version.md#целевая-модель-полного-редактора).

| Приоритет | Задача | Как проверить готовность |
| --- | --- | --- |
| 1 | Сохранять изменения нескольких линий и выборочно откатывать геометрию | После повторного входа видны обе линии. Откат одной сохраняет правку другой. |
| 2 | Перемещать, добавлять и удалять вершины участков, корректировать концы и положение точечных объектов | Редактор меняет двухточечную и многовершинную линии и положение оборудования в одном наряде. |
| 3 | Создавать, менять свойства и удалять участки, узлы и оборудование | Новый объект имеет устойчивый код и идентификатор. После исправления свойства узнаётся тот же экземпляр. |
| 4 | Создавать, менять и удалять соединения объектов | После повторного входа видны тип связи и оба её конца. Удаление объекта требует разрешить действующие связи. |
| 5 | Принять редактор на смешанном наборе изменений | Создание, правка, удаление, перепривязка, повторное чтение и восстановление согласованы в одной рабочей версии. |
| После приёмки 1–5 | Анализ путей и состояния сети, затем доказательства готовности и ReviewPackage, решение Reviewer, допуск и история публикации | Сравнение путей объясняет изменение связности. Подтверждённый пакет и актуальность основания позволяют отдельно решить вопрос о публикации. |

**Уже реализовано для первого учебного среза.** Persisted first-save, Save/Revert, согласованное чтение и S2-X01 recovery сохраняют значение как регрессионная основа. Сверка L-003 от 08.11 относится к экземпляру revision 49. В действующем интерфейсе редактируется линия из трёх вершин. Повторная квалификация другого набора и позиционное доказательство для review учитываются на соответствующем этапе. При снятии лимитов прежде всего проверяются совместимость старых рабочих версий и исходов команд, защита от устаревшей записи и граница AOI.

Отзыв и коррекция учитываются в цикле публикации. Прочие открытые правила, включая restart и архивные удержания, остаются в FU-2026-10-13-004. Результаты новой очереди получают статус реализации только после отдельной разработки и проверки.

## Superseded Draft Summary

Первичный каркас доменной модели создан. Содержательная инициализация выполняется отдельным проходом по существующим raw, Vision_wiki, Code_wiki и sprint/release документам.

## Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет зафиксированных конфликтов в новом слое | Полнота модели пока не оценена | draft | Выполнить первичную инициализацию доменной модели |

## Coverage

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | draft | Требуется извлечение из текущих источников |
| Subdomains | draft | Требуется классификация core/supporting/generic |
| Bounded Contexts | draft | Требуется привязка к текущей модели данных и коду |
| Aggregates | draft | Требуется проверка инвариантов |
| Commands And Events | draft | Требуется связать команды, события и политики |
| Sprint Planning Inputs | draft | Требуется список вопросов для 14-дневного спринта |

## Историческая Discovery Queue — superseded

Правила следующего запуска определяет `.agents/skills/source-command-discover/SKILL.md`. Актуальные вопросы и ссылки на решения приведены в Current Discovery Queue выше.

## Актуализация После Research 2026-10-13

[[RAW_inputs/research_results/2026-10-13-utility-gis-editor-expert-recovery-governance]] обработан как синтез экспертных предложений. В [[Wiki/_registry/questions]] сейчас 8 открытых вопросов; в [[Vision_wiki/decisions/followups/index]] — 22 открытых follow-up'а. Новых активных blocking conflicts нет. Ранее принятые правила не пересмотрены.

Новый proposed use case [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] описывает организационную передачу и критерии продолжения. Он не создаёт новый bounded context/aggregate и не меняет транзакционные границы WorkOrder/EditVersion. Требуют принятия правила разбора/исходных дефектов, применимости evidence и объяснения правки; confidence medium.

Ни один реальный сотрудник, SLA, specification/допуск, measurement evidence или срок хранения этим research не установлен. Метка stale сохраняется: прежняя очередь fixture/metadata и описания реализации выше по-прежнему требуют отдельной сверки. Не считать новые предложения выполненным S2-X01, repair/restart workflow или позиционной приёмкой.

## Историческое уточнение: решения условной организации 2026-10-13

Этот раздел заменяет прежние выводы об отсутствии реальных ответственных/specification/records policy и ожидании принятия новых предложений. [[RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions]] принимает правила модели, а не подтверждает их реализацию. [[Wiki/conflicts/2026-10-13-real-organization-vs-simulated-decisions]] resolved. В questions остаются 2 вопроса сверки metadata/fixture; follow-up open: 19. Активных канонических blocking conflicts: 0.

[[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] active. Новых агрегатов, auth roles, событий или длительных транзакций нет. SIM-UGIS-POS-001 задаёт учебную точность; SIM-UGIS-RET-001 — сроки. Existing first-save UNVERIFIED, topology not_checked и downstream guards сохранены. Legacy сведения выше исторические; фактическая реализация/metadata требуют отдельной сверки по FU-2026-10-11-001 и FU-2026-10-13-004, stale не снят.

## Актуальное уточнение после ingest 2026-10-16

[[RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research]] добавил [[Wiki/specifications/editing_resumption_allowed]] и уточнил recovery policy/use case/state machine без новых aggregates, server states и auth roles. 15 ответов зафиксированы как решения условной организации; новых активных blocking conflicts нет. Два прежних вопроса metadata/fixture остаются открытыми до явной сверки реестра; source-level основания уже описаны в [[Code_wiki/архитектура/edit_geometry_fixture_metadata]].

Технический ingest Save/recovery выполнен: [[Code_wiki/архитектура/edit_version_save_orchestration]], [[Code_wiki/архитектура/frontend_save_recovery]]. Старые требования повторить этот ingest ниже/выше исторические. Метка stale сохраняется из-за несогласованной очереди реализации и metadata/fixture. Отсутствие прямого component-вызова recovery не означает отсутствие пути: store вызывает restorePendingSave из open/restore. UI Save/Revert и явное продолжение после access block требуют отдельной реализации/приёмки; S2-X01 не закрыт.

## Пригодность данных и границы вычисления — 2026-10-16

[[RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research]] добавил сценарий [[DDD_Wiki/use_cases/assess_saved_line_quality]] и два канонических узла: [[Wiki/policies/demo_dataset_qualification_policy]], [[Wiki/specifications/saved_line_quality_assessment]]. Критерий SIM-UGIS-POS-001 не меняется; уточнено доказательство прохождения/несоответствия при численной неопределённости, смешанные причины неприёмки и привязка к состоянию.

Остаются 2 open metadata/fixture, 19 open follow-up и 0 активных канонических blocking conflicts. Новые ответы не доказывают фактическую БД, runtime acceptance или готовность reviewer/evaluator. Stale сохраняется до существующей сверки FU-2026-10-11-001. Следующий discovery не должен повторять эти 15 правил; следующий шаг — сверка паспорта и реализации в пределах отдельных задач.

## Смысл правки и сетевые последствия — 2026-10-16

[[RAW_inputs/research_results/2026-10-16-utility-gis-editor-network-semantics-research]] уточняет существующий workflow через [[Wiki/glossary/network_edit_meaning]] и [[Wiki/policies/network_edit_semantics_policy]]. Новые aggregate/state/API не вводятся. Предметные ответы приняты для условной организации, runtime и фактическая БД не подтверждены. Остаются 19 open follow-up, 2 вопроса metadata/fixture и 0 активных канонических blocking conflicts; stale сохраняется по FU-2026-10-11-001.

## Осознанная правка и доказательство — 2026-10-18

[[DDD_Wiki/use_cases/prepare_and_check_line_edit]] уточняет существующий workflow. Два новых предметных понятия и критерий упражнения не расширяют ближайший scope до asset lifecycle, field sync или hydraulic simulation. Корпус 81 документа — [[RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis]]. Ответы приняты за условную организацию, runtime и фактическая БД не проверены. Сохраняются 19 open follow-up, два metadata/fixture вопроса и 0 активных канонических blocking conflicts; stale не снят.

## Пересмотр основания — актуальное уточнение 2026-10-19

[[DDD_Wiki/use_cases/reassess_line_edit_basis]] связывает новый источник/редакцию, зависимости evidence и повторную оценку текущего результата. Правила приняты за условную организацию по двум новым RAW, общий корпус — 77 документов; не интервью и не runtime-приёмка. Нет новых aggregates, events или guards Save. Открыты прежние 19 follow-up и два metadata/fixture вопроса; активных канонических conflicts 0, stale сохраняется.

## Уточнение модели заключения — 2026-10-22

По [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-research]] и [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]] добавлены [[Wiki/concepts/assessment_statement_lifecycle]], [[Wiki/concepts/assessment_delivery_and_acceptance]], [[Wiki/policies/assessment_issue_and_correction_policy]], [[Wiki/specifications/assessment_statement_usable]] и [[DDD_Wiki/use_cases/issue_and_correct_line_assessment]]. Приняты 15 решений условной организации на корпусе 84 документов. Отделены выпуск от pass, применимость от current geometry, доставка от приёмки; границы частичного результата и исправления сформулированы явно.

Это повышение определённости модели, не готовность evaluator, journal, archive или review/post. Новых blocking conflicts нет; два metadata/fixture вопроса, FU-2026-10-13-004, S2-X01 и stale-маркер сохраняются. Позиционный критерий, baseline, guards и retention неизменны. Литература не подтверждает фактическую БД или пригодность L-003.
