---
title: Индекс Знаний GeoService
type: index
status: active
created: 2026-05-30
updated: 2026-06-28
source: null
tags: [knowledge, index, geoservice]
---

# Индекс Знаний GeoService

Это точка входа в project knowledge wiki GeoService.

## Проект

- Название: GeoService
- Репозиторий: `C:\Repositories\geoservice`
- Стадия: идея / прототип
- Кратко: GeoService хранит геообъекты в PostGIS, отдает их через FastAPI и отображает/редактирует карты через Vue и MapLibre.

## Области Знаний

- [[RAW_inputs/index]] - сырые источники и исходные материалы проекта.
- [[Wiki/index]] - канонические доменные сущности, concepts, actors, commands, events, policies, specifications, conflicts, questions и registry tables.
- [[DDD_Wiki/index]] - DDD-модель: domains, subdomains, bounded contexts, context map, aggregates, invariants, use cases, integration patterns и model health.
- [[Vision_wiki/index]] - продуктовые знания, решения, конфликты, follow-up'ы и заметки встреч.
- [[Code_wiki/index]] - техническая wiki для архитектуры, разработки, deployment и состояния проекта.
- [[memory/project-state]] - живое состояние проекта.
- [[memory/llm-wiki-method]] - методика ведения атомарных LLM-wiki нод.
- [[docs/agent-memory/README]] - компактная инженерная память Codex.

## Свежие Изменения

- 2026-05-30: Создана стартовая project knowledge wiki и ручной pipeline `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`.
- 2026-05-30: Выполнен `/ingest repository-snapshot`; техническая карта текущего репозитория добавлена в [[Code_wiki/index]].
- 2026-05-30: Выполнен `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после repository snapshot.
- 2026-05-30: Обработан RAW source `RAW_inputs/documents/спринт 1.odt`; заполнены Release 1 solution-ноды и desired API contract.
- 2026-05-31: Первый `/discover` и фаза Ф1 уточнили pet-project контекст, исследовательскую мотивацию и отсутствие подтвержденной внешней пользовательской боли.
- 2026-06-01: Выполнен `/sync-vision`; корневой индекс и [[memory/project-state]] синхронизированы после Release 1 ingest и Ф1 discovery.
- 2026-06-01: Обработан research RAW source `RAW_inputs/documents/Ф2.md`; добавлены модели collaborative editing, пользовательские архетипы и карта альтернатив для подготовки Ф2-Ф3.
- 2026-06-02: Выполнен `/sync-vision`; корневой индекс и [[memory/project-state]] синхронизированы после ingest исследования Ф2.
- 2026-06-02: `/discover --phase Ф2` сузил исследование до двух модельных authoritative editing сценариев: `Utility GIS editor` и кадастровый инженер.
- 2026-06-02: Выполнен повторный `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после discovery Ф2.
- 2026-06-02: Второй проход `/discover --phase Ф2` выбрал `Utility GIS editor` как primary research-persona; кадастровый сценарий отложен.
- 2026-06-03: Выполнен `/sync-vision`; подтверждены отсутствие новых RAW inputs, 8 открытых follow-up'ов, отсутствие stale-нод и ожидаемый lint-конфликт `FU-2026-06-01-004`.
- 2026-06-03: Обработан RAW source `RAW_inputs/documents/03.06.2026deep-research-report.md`; Ф3 сравнила альтернативы для `Utility GIS editor`, baseline - `ArcGIS Enterprise + Utility Network`, niche GeoService - conflict/review explainability.
- 2026-06-04: Выполнен `/sync-vision`; подтверждены актуальность индексов после Ф3, отсутствие новых необработанных RAW inputs, 7 открытых follow-up'ов, отсутствие stale-нод и ожидаемый lint-конфликт `FU-2026-06-01-004`.
- 2026-06-04: `/discover --phase Ф4` зафиксировал demo-scope: focused conflict/review layer для `Utility GIS editor`, primary scenario `geometry/association conflict`, роли `Editor`/`Reviewer`, synthetic utility dataset и explicit non-goals.
- 2026-06-05: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; уточнены end-to-end walking skeleton, desired technical skeleton и конкретный dataset `synthetic_utility_feeder_01`.
- 2026-06-05: Выполнен `/sync-vision`; индексы актуальны после latest ingest, новых необработанных RAW inputs нет, открытых follow-up'ов 4, stale-нод не обнаружено.
- 2026-06-05: `/discover --phase Ф5` зафиксировал local Docker Compose rollout для developer demo: decision maker - владелец pet-проекта, ценность - `learning value`, главный rollout-риск - непонятный UI conflict review.
- 2026-06-06: Выполнен `/sync-vision`; индексы синхронизированы после Ф5 и repository-change ingest, новых необработанных RAW inputs нет, открытых follow-up'ов 6, stale-нод не обнаружено.
- 2026-06-06: `/discover --phase Ф6` зафиксировал NFR local demo: Chrome, reference hardware с 16 GB RAM, startup/reset за несколько минут, JWT, separation of duties, audit persistence и минимальную observability.
- 2026-06-06: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_target_times.md`; добавлены draft P95 acceptance targets и performance benchmark follow-up.
- 2026-06-07: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`; добавлены канонический словарь `Utility GIS editing`, source summary и desired technical vocabulary без расширения demo-scope.
- 2026-06-07: Выполнен `/sync-vision`; индексы актуальны после Ф6 и двух RAW ingest, необработанных RAW inputs и stale-нод нет, открыты 7 follow-up'ов.
- 2026-06-07: `/discover --phase Ф7` зафиксировал `Safe Authoritative Post Rate >=95%` на 200 work orders, safety blockers, manual baseline, 30 benchmark runs и порядок минимальных экспериментов.
- 2026-06-11: Выполнен `/sync-vision`; индексы актуальны после Ф7 и repository-change ingest, новых необработанных RAW inputs и stale-нод нет, открыты 9 follow-up'ов.
- 2026-06-11: `/discover --phase Ф8` пересобрал Release 1 вокруг полного `Utility GIS editor` workflow; старый generic GIS сохранен только как технический foundation.
- 2026-06-11: Подготовлены code compliance matrix и план реализации нового Release 1 на 7 двухнедельных спринтов.
- 2026-06-12: Спринт 1 разложен на 14 календарных дней; контракты Дня 1 зафиксировали acceptance AC-01..AC-07, доменную модель, API и вертикальный backlog S1-01..S1-10 в `docs/sprint_1`.
- 2026-06-12: Выполнен `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после Ф8 и планирования Спринта 1, новых RAW inputs и stale-нод нет, открыты 10 follow-up'ов.
- 2026-06-12: Обработана синтетическая репетиция интервью `Utility GIS editor`; primary persona и JTBD приняты для design, добавлен акцент на единый evidence context, внешний user validation отложен.
- 2026-06-13: Реализованы роли `Editor`/`Reviewer`, DB-backed active-user auth, structured auth errors, demo seed и reviewer shell Дня 2 Спринта 1; связанные ноды [[Code_wiki/index]] синхронизированы через `/ingest repository-change`.
- 2026-06-13: Agent memory и knowledge pipeline переведены на gate устойчивого знания, компактный реестр изменений `Code_wiki` и read-only memory audit.
- 2026-06-13: Выполнен `/sync-vision`; необработанных RAW inputs и stale-нод нет, открыты 10 follow-up'ов, ожидаемый lint-конфликт остаётся на 12 неизменяемых RAW Markdown files.
- 2026-06-13: Обработаны синтетическая репетиция `Utility GIS reviewer` и broad-domain репетиции editor/reviewer; добавлены reviewer persona, JTBD, checklist реального интервью и вопросы о границах reviewer role.
- 2026-06-14: Выполнен `/sync-vision`; все 19 RAW sources обработаны, открыты 13 follow-up'ов, stale-ноды не обнаружены, ожидаемый lint-конфликт охватывает 18 неизменяемых RAW Markdown files.
- 2026-06-14: Assistant-led chat workshop по `geometry/association conflict` помечен superseded; доверенный RAW source `utility_gis_editor_geometry_association_conflict_answers.md` стал канонической основой planned routing следующего релиза. Текущий Release 1 оставлен без изменений.
- 2026-06-15: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с utility schema, seed `synthetic_utility_feeder_01`, read-only feeder API, startup order и тестовым покрытием.
- 2026-06-16: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с package boundaries `utility_service`, Docker/CI contract `utility_service` и новой раскладкой backend tests.
- 2026-06-16: Выполнен `/sync-vision`; новых RAW inputs и stale-нод нет, открыты 13 follow-up'ов, ожидаемый lint-конфликт остается на 18 неизменяемых RAW Markdown files.
- 2026-06-16: Обработан RAW source `RAW_inputs/meetings/Reviwer Decision.md`; Release 2 reviewer decision уточнен как package approval for post readiness, approval/post authorization разделены, trace-boundary conflict закрыт для planned policy.
- 2026-06-17: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с backend foundation `WorkOrder`: таблица `utility_network.work_orders`, seed `WO-001`, assignment/status rules и unit coverage.
- 2026-06-17: Выполнен `/sync-vision`; новых RAW inputs и stale-нод нет, открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 19 неизменяемых RAW Markdown files.
- 2026-06-17: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f1.md`; уточнен why-now Release 2 для `geometry/association conflict`, границы `Normal`/`High`/`Critical`, risk переусложнения и validation caveats.
- 2026-06-18: Выполнен `/sync-vision`; новых RAW inputs и stale-нод нет, открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 20 неизменяемых RAW Markdown files.
- 2026-06-18: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f2.md`; уточнен primary user `Editor`, момент боли и safe post criteria для Release 2 `geometry/association conflict`.
- 2026-06-19: Выполнен `/sync-vision`; новых RAW inputs после учтенного ingest Ф2 и stale-нод нет, открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 21 неизменяемый RAW Markdown file.
- 2026-06-19: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f3.md`; уточнен конкурентный baseline `ArcGIS native + SOP + экспертный handoff`, good-enough зоны baseline и demo proof для unified evidence context Release 2.
- 2026-06-20: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с новой границей модели данных: `user.users`, `utility_network` для актуальной сети и per-WorkOrder `DefaultState`, `work_order` для `WorkOrder`/`EditVersion`, repository-only связи, `baseNetworkRevision` API contract и seed/CI notes.
- 2026-06-20: Выполнен `/sync-vision`; новых RAW inputs и новых Vision/Code_wiki нод нет, обновления Code_wiki от repository-change ingest отражены в индексе и [[memory/project-state]], открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 22 неизменяемых RAW Markdown files.
- 2026-06-20: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f4.md`; Ф4 сузила Release 2 demo до transformer terminal association scenario, read-only consequence package, routing/audit object и stale/failure case.
- 2026-06-20: Обработан RAW source `RAW_inputs/documents/UtilityGisEditorRole.md`; уточнена реальная практика роли как owner/editor of authoritative utility network changes, два основных tooling stacks, field sync, topology QA, training и KPI.
- 2026-06-21: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с переносом AOI в bounded context `work_order`, Workspace API и фильтрацией edit-version workspace по `WorkOrder.scope.aoi`.
- 2026-06-22: `/ingest repository-change` синхронизировал [[Code_wiki/index]] с repair/idempotent migration contract для schema-boundary откатов и stamped dev/CI volumes.
- 2026-06-22: Выполнен `/sync-vision`; новых RAW inputs, новых Vision нод и stale-нод нет, открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 24 неизменяемых RAW Markdown files.
- 2026-06-22: `/discover --context "geometry/association conflict" --phase Ф5` зафиксировал internal developer demo rollout для Release 2 и следующий артефакт `implementation contract`.
- 2026-06-22: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f5.md`; Ф5 уточнила value signal, placement after reconcile, rollout roles, support package и допустимые claims для Release 2 `geometry/association conflict`.
- 2026-06-23: Выполнен `/sync-vision`; RAW source Ф5 уже обработан и отражен в индексах, новых необработанных RAW inputs и stale-нод нет, открыты 12 follow-up'ов, ожидаемый lint-конфликт остается на 25 неизменяемых RAW Markdown files.
- 2026-06-23: `/discover --context "geometry/association conflict" --phase Ф6` подготовил checklist ограничений и NFR для Release 2 `implementation contract`.
- 2026-06-23: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f6.md`; Ф6 уточнила implementation contract boundary, computed evidence, state machine, stale rules, hard blockers, audit object, API/events, P95 и observability для Release 2 `geometry/association conflict`.
- 2026-06-23: `/discover --context "geometry/association conflict" --phase Ф7` подготовил checklist метрик, рисков, experiments и guardrails для проверки Release 2 consequence package.
- 2026-06-23: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f7.md`; Ф7 зафиксировала `contract readiness pass rate`, zero false-safe guardrail, secondary metrics, stale/pre-post sidecar experiment, run data, manual baseline и course-change criteria для Release 2 `geometry/association conflict`.
- 2026-06-23: `/discover --context "geometry/association conflict" --phase Ф8` подготовил closeout checklist для Release 2: ready-to-implement decisions, remaining blockers, RAW artifacts, wiki updates и следующие шаги перед implementation contract.
- 2026-06-23: Обработан RAW source `RAW_inputs/meetings/geometry_association_conflict_f8.md`; Ф8 закрыла discovery Release 2 как pre-post decision-support layer, отделила contract-ready decisions от human-validation hypotheses и задала следующий артефакт implementation contract v0.1.
- 2026-06-24: Обработан RAW source `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; уточнены `Reviewer` как semantic approval, `Publisher` / demo-system action как technical post, `ReviewPackage`, state machine, risk tiers, stale policy, hard blockers и audit boundary.
- 2026-06-24: Добавлен канонический доменный слой [[Wiki/index]] и DDD-модель [[DDD_Wiki/index]]; `Wiki/_registry` и [[DDD_Wiki/model_health]] отражают review/post model, active coverage и resolved conflicts.
- 2026-06-26: Выполнен `/sync-vision`; все 30 RAW sources обработаны, `Wiki/_registry` совпадает с фактическими нодами, новых необработанных RAW inputs и stale-нод нет, открыты 15 follow-up'ов, ожидаемый lint-конфликт остается на 29 RAW Markdown files.
- 2026-06-26: Обработан RAW source `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; новый review/post contract должен быть отдельным integrated artifact, старый Release 2 contract legacy/reference, ближайший путь: `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`, планирование маленькими спринтами.
- 2026-06-27: Выполнен `/sync-vision`; учтены ingest `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` и Day 13 repository-change ingest, `Wiki/_registry` совпадает с фактическими нодами, новых необработанных RAW inputs и stale-нод нет, открыты 16 follow-up'ов, ожидаемый lint-конфликт остается на 30 RAW Markdown files.
- 2026-06-27: Обработан RAW source `RAW_inputs/meetings/increment_after_open_workspace.md`; ближайший sprint начинается с persisted edit slice, добавлены [[Wiki/commands/update_edit_version_feature]], [[Wiki/specifications/edit_version_has_persisted_change_set]], [[Wiki/domain_events/edit_version_feature_updated]] и resolved conflict [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]].
- 2026-06-28: Выполнен `/sync-vision`; учтено post-sync изменение `b8f0740`, `Wiki/_registry` совпадает с фактическими нодами, новых необработанных RAW inputs и stale-нод нет, открыты 16 follow-up'ов, ожидаемый lint-конфликт остается на 31 RAW Markdown files.
- 2026-06-28: Обработан RAW source `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; first persisted edit slice уточнен до geometry diff существующей line feature, добавлены [[Wiki/commands/update_edit_version_feature_geometry]], [[Wiki/domain_events/edit_version_change_set_persisted]], [[Wiki/specifications/edit_version_basic_draft_validation]], [[Wiki/value_objects/draft_version_token]] и [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]].

## Открытые Вопросы

- Новый Release 1 разбит на 7 двухнедельных спринтов; в Спринте 1 уже готовы роли/доступ, utility schema, `synthetic_utility_feeder_01`, read-only feeder API, `WorkOrder`, создание `EditVersion` из per-WorkOrder `DefaultState`, экран `Мои наряды`, Edit Workspace и full path API smoke; следующий scope - persisted edit slice: geometry diff существующей line feature, `UpdateEditVersionFeatureGeometry`, readback persisted feature + diff, normalized `operation`, `DraftVersionToken` и basic draft validation flags.
- Для `Utility GIS editor` нужно реализовать полный путь work order -> edit version -> validation -> reconcile -> conflict resolution -> review -> post -> audit на `synthetic_utility_feeder_01`.
- Нужно восстановить доступные URL для non-Esri vendor-specific утверждений из research по collaborative editing.
- Нужно согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset/`full-clean` scripts, demo сценарий, troubleshooting, observability minimum и `import GeoJSON`.
- Нужно проверить draft P95 targets на `synthetic_utility_feeder_01` в Chrome на reference hardware.
- Нужно снять manual baseline на 10-20 work orders и провести product evaluation на 200 started work orders с 7-дневным correction window.
- Нужно провести реальные интервью с `Utility GIS editor` и `Reviewer`; для reviewer проверить planned policy: package approval vs technical `post`, routing по специализации, совмещение ролей, обязательность approve comment и user validation trace-boundary.
- Для Release 2 нужно проверить, снижает ли consequence-first explanation внешние проверки и time-to-confident-decision по `geometry/association conflict`, и не дублирует ли UI обычный Conflicts view.
- Для Release 2 Ф4 demo нужно проверить canonical transformer terminal association scenario, package evidence, `Normal/High/Critical` tiers без преждевременного `Simple`, stale decision handling и audit object.
- Нужно подготовить отдельный integrated review/post implementation contract v0.1 для developer demo: `submit_for_review`, `ReviewPackage`, reviewer decision, computed `can_post`, pre-post check, simulated post, durable audit, system `post-gate`, safety-complete veto set, `DefaultChangedAfterReconcile`, zero false-safe gate и small-sprint rollout через существующий `WorkOrder` / `EditVersion` flow.
- Для Release 2 Ф7 нужно подготовить measurement harness: scripted golden walkthrough, 10 deterministic repeats, 10 stale/blocker/pre-post mutations, optional 30 automated runs и manual baseline против `ArcGIS native Conflicts view + SOP + expert handoff`.
- Для Release 2 нужно подготовить отдельный real validation checklist для `Editor`/`Reviewer`: risk wording, authority matrix, sample review для `Normal`, evidence sufficiency, repeat-review UX и trust к blocker verdict.
- Технические пробелы repository snapshot зафиксированы в [[Code_wiki/состояние_проекта/repository_snapshot]].
- Очередь follow-up'ов: [[Vision_wiki/decisions/followups/index]].

## Ручной Pipeline

- Утро: запустить `/sync-vision`, прочитать `memory/project-state.md`, проверить новые файлы в `RAW_inputs/`, затем запустить `/ingest` для новых RAW inputs.
- Перед встречей: запустить `/discover --context "планирование спринта" --phase "F2"` и подготовить чек-лист из 10-15 вопросов.
- Планирование спринта: запустить `/plan-sprint`; команда использует текущий код, `Code_wiki`, `Wiki/DDD_Wiki`, конфликты модели, генерирует 150 planning questions и показывает top 15 для 14-дневного спринта.
- После встречи: положить транскрипт в `RAW_inputs/meetings/`, запустить `/ingest`, обновить wiki-ноды, конфликты, follow-up'ы и project state.
- Раз в неделю: запустить `/lint-wiki`, затем `/sync-vision`, затем проверить отчет о здоровье wiki.

## Repository Ingest

`/ingest repository-snapshot` фиксирует уже существующее состояние репозитория в `Code_wiki` без привязки к `git diff`.

`/ingest repository-change` запускается только когда завершённая работа содержит
новое устойчивое техническое знание для `Code_wiki`. Завершение плана, commit
или успешные тесты сами по себе не являются триггерами. Pre-commit не запускает
и не проверяет repository-change ingest.
