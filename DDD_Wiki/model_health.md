---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-10-22
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md; RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research.md; RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research.md; RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-answers.md"
tags: [domain-knowledge, ddd, health, stale]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Актуальность Состояния

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

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, review/post и audit. Discovery answers закрыли поведение first-save contract, но фактические demo metadata и fixture ещё не выбраны. Ближайшая реализация должна доказать путь workspace -> `UpdateEditVersionFeatureGeometry` -> сдвиг ровно одной внутренней вершины одной существующей line feature -> server-side canonicalization по metadata dataset -> atomic save full resulting snapshot относительно единого базового состояния работы -> command response + persisted readback -> revert к baseline. Line должна быть valid/simple и `covered by` AOI; endpoints, structure, attributes и associations заморожены. Позиционная точность для приёмки берётся из утверждённой спецификации и evidence, coordinate grid — из spatial-reference metadata dataset; это разные правила. `POSITIONAL_ACCURACY_UNVERIFIED` разрешает technical save, но блокирует review/completion/post. `DraftVersionToken` защищает весь aggregate, а `CommandId` идентифицирует одну operation на весь lifecycle `EditVersion`, включая concurrent retry и повтор terminal rejection. `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff и хранит line identity + before/after + actor/time/baseline/command evidence; `EditVersionChangeSetCleared` возникает на revert; no-op/retry событий не создают. First-save readiness называется `persisted-draft-ready`: lifecycle остается `open`, topology - `not_checked`, review/post остается downstream context.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет активных blocking conflicts | - | clear | Сопоставить принятые решения с S2-X01 по FU-2026-10-13-004 и сверить metadata/fixture по FU-2026-10-11-001 |

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

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | active | [[Wiki/glossary/utility_gis_editing]], [[Wiki/glossary/positional_accuracy_for_acceptance]], [[Wiki/glossary/coordinate_storage_precision]] и [[Wiki/glossary/base_work_state]] закрепляют язык workflow, точности и baseline. |
| Subdomains | active | Core subdomain [[DDD_Wiki/subdomains/utility_authoritative_editing]] отделен от generic map editing. |
| Bounded Contexts | active | Выделены контексты Work Order, Utility Network, Review Post, Audit и Auth. |
| Context Map | active | [[DDD_Wiki/context_map/geoservice_context_map]] описывает upstream/downstream и границу application layer. |
| Aggregates | active | `WorkOrder`, `EditVersion` и `ReviewPackage` активны в доменной модели. |
| Commands And Events | active | `OpenEditVersion` активна; first write command - `UpdateEditVersionFeatureGeometry`; события `EditVersionChangeSetPersisted` и `EditVersionChangeSetCleared` описывают save/revert, `CommandId` отделяет retry от concurrency. |
| Policies And Specifications | active | Проверка назначения, [[Wiki/policies/edit_geometry_precision_policy]], [[Wiki/policies/positional_accuracy_acceptance_policy]], persisted change set, basic draft validation, ready-for-review, post allowed, review/post и stale policies активны. |
| Sprint Planning Inputs | active | `Wiki/_registry/questions.md` содержит приоритетные вопросы для планирования маленьких спринтов. |

## Current Discovery Queue

Основные доменные развилки first save закрыты. Следующий `/discover` не должен заново спрашивать snapshot-vs-diff, one-internal-vertex guard, AOI boundary, token/idempotency semantics, event cadence, baseline naming/mapping или состав event evidence. По [[Wiki/_registry/questions]] открыты 2 вопроса сверки с существующим кодом и Sprint 2:

- Какие фактические CRS, coordinate unit, `xyResolution`, `xyTolerance`, origin/domain и transformations имеет сохраняющий demo dataset?
- Как выбранная в seed eligible line `L-003` и её before/after fixture coordinates соответствуют принятым критериям? Вопрос не закрывается без содержательной сверки по `FU-2026-10-11-001`.

Учебная positional specification и records policy уже приняты: [[Wiki/specifications/simulated_line_positional_acceptance]] и [[Wiki/policies/change_history_retention_policy]]. Их реализация и привязка evidence к L-003 не подтверждены этой синхронизацией.

Human-layer вопросы по `Reviewer`, evidence sufficiency, policy-relevant `traceResult` / `subnetworkStatus` важны после реализации persisted draft path.

## Current Sprint Planning Queue

Следующий `/plan-sprint` должен использовать 14-дневную рамку, но мыслить маленькими вертикальными increments:

- Первый спринт после открытия workspace создает end-to-end first-save slice для одной line feature и одной внутренней вершины: сначала фиксирует реальную editable fixture и spatial metadata dataset, затем добавляет единое immutable базовое состояние работы + current snapshot, AOI `CoveredBy`, server-side canonical single-vertex normalization, hard atomic guards, явный `POSITIONAL_ACCURACY_UNVERIFIED`, aggregate `DraftVersionToken`, lifecycle registry `CommandId`, before/after event evidence, response/readback proof, no-op semantics, stale recovery и revert с двумя domain events.
- Следующий спринт добавляет `submit_for_review` и `ReviewPackage v0.1` как materialized snapshot поверх persisted `edit_version_features`, с backrefs на исходные rows и editor summary/evidence.
- Следующий спринт добавляет reviewer detail view одного package, reviewer decision и computed `can_post`; simulated post, durable audit, trace/subnetwork evidence, risk tiers, reviewer queue и association mutation не должны стартовать раньше persisted change set.

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

## Discovery Queue

Следующий `/discover` должен сгенерировать 150 candidate questions по пробелам модели и выбрать top 15 для пользователя.

## Актуализация После Research 2026-10-13

[[RAW_inputs/research_results/2026-10-13-utility-gis-editor-expert-recovery-governance]] обработан как синтез экспертных предложений. В [[Wiki/_registry/questions]] сейчас 8 открытых вопросов; в [[Vision_wiki/decisions/followups/index]] — 22 открытых follow-up'а. Новых активных blocking conflicts нет. Ранее принятые правила не пересмотрены.

Новый proposed use case [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] описывает организационную передачу и критерии продолжения. Он не создаёт новый bounded context/aggregate и не меняет транзакционные границы WorkOrder/EditVersion. Требуют принятия правила разбора/исходных дефектов, применимости evidence и объяснения правки; confidence medium.

Ни один реальный сотрудник, SLA, specification/допуск, measurement evidence или срок хранения этим research не установлен. Метка stale сохраняется: прежняя очередь fixture/metadata и описания реализации выше по-прежнему требуют отдельной сверки. Не считать новые предложения выполненным S2-X01, repair/restart workflow или позиционной приёмкой.

## Текущее уточнение: решения условной организации 2026-10-13

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
