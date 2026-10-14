---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-10-13
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущая доменная модель строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Живое Состояние Pipeline

- Режим согласован 2026-10-13: агент через `02_expert_oldman_ufa` представляет условную организацию, исследует практику и выбирает доменные решения. Реальной организации нет. Требования реальных назначений, интервью и внутренних документов ниже и в прежних follow-up не являются блокерами; соответствующие вопросы нужно решать для модели. Внешние факты, решения модели и гипотезы различаются. См. [решение о режиме](../docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md).

- Канонический доменный слой: `Wiki/` и `DDD_Wiki/`; `Vision_wiki` остается legacy/source слоем, `Code_wiki` хранит устойчивое техническое знание.
- Ближайший доменный инкремент уточнен: persisted edit slice в `WorkOrder` / `EditVersion` через `UpdateEditVersionFeatureGeometry` для одной line feature и одной внутренней вершины, единое базовое состояние работы, server-side canonicalization по actual dataset metadata, AOI `CoveredBy`, atomic guards, явный `POSITIONAL_ACCURACY_UNVERIFIED`, `DraftVersionToken`, lifecycle-safe `CommandId`, before/after evidence, command response + durable readback и revert. Review/post требует verified positional acceptance после устойчивого change set.
- Последний RAW ingest: 2026-10-13, `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md`; все 15 ответов пересмотрены, решения приняты агентом по прямому поручению пользователя. Внешние факты и синтетическое evidence отделены от правил модели.
- Последний `/ingest repository-change` по реестру: 2026-10-12, публичный Save API и согласованный workspace readback — [[../Code_wiki/архитектура/edit_version_api_readback]].
- Последний `/sync-vision`: 2026-10-13 20:33 +05:00 (Asia/Qyzylorda).

## Состояние Wiki На 2026-10-13

- RAW inputs: 41 файл, все отражены в `RAW_inputs/index.md`; новых и необработанных RAW inputs нет.
- Новейшее доменное пополнение: активные политики разбора, исходных дефектов, позиционной приёмки, пояснений и хранения; [[../Wiki/specifications/simulated_line_positional_acceptance]] (SIM-UGIS-POS-001 v1.0) и активный [[../DDD_Wiki/use_cases/interrupted_edit_work_recovery]]. Active означает принятие решения, не реализацию.
- `Wiki/_registry` соответствует активным нодам; superseded-ноды не требуют включения в активные реестры.
- Открытые follow-up'ы: 19; полный список — [[../Vision_wiki/decisions/followups/index]]. В [[../Wiki/_registry/questions]] остаются 2 вопроса сверки metadata/fixture с существующим кодом; шесть вопросов решений организации отвечены.
- Активные blocking conflicts в каноническом `Wiki`: 0; [[../Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]] разрешён решением пользователя 2026-10-12. Legacy conflict [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] остается active до docs-синхронизации `FU-2026-06-11-002`.
- Stale-ноды: 5 — [[../Code_wiki/архитектура/backend]], [[../Code_wiki/архитектура/edit_version_persistence]], [[../Code_wiki/архитектура/edit_geometry_determinism]], [[../Code_wiki/архитектура/data_model]] и [[../DDD_Wiki/model_health]]. Причины — отставание описаний Save service, HTTP-границы, workspace decoding и очереди fixture/metadata; см. `FU-2026-10-11-001`.
- Последняя проверка `lint-wiki.py`: 2026-10-13 после ingest экспертного research. Обнаружены только 37 известных `missing_frontmatter` в неизменяемых RAW Markdown files; проблем вне `RAW_inputs/` нет. Follow-up `FU-2026-06-01-004` остается открытым.

## Требует Внимания

- FU-2026-10-13-001/002/003 и FU-2026-10-11-003 закрыты решениями условной организации. Реализация отдельно: FU-2026-10-13-004. Требования реальных сотрудников и документов сняты; исторические RAW сохранены.

- Принятые правила восстановления и D5-Q1 отражены в [S2-X01](../docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md), статус «запланировано». Новые правила организации нужно сопоставить с этим планом отдельной задачей. SIM-UGIS-POS-001 задаёт 0,50 м для учебного evidence; SIM-UGIS-RET-001 — 10 лет истории/архива, 3 года карточек, 30 дней debug с удержаниями. Автоочистка выключена.

- `Code_wiki` частично синхронизирован в октябре, но внутренний backend Save/Revert, registry/replay, terminal rejection и события от 2026-10-11 требуют отдельного `/ingest repository-change`. Также нужна проверка покрытия июльских frontend-изменений и более поздних fixtures/schema/history; сам факт октябрьского ingest не подтверждает их полноту. Публичный Save/readback уже описан ingest от 2026-10-12; для старых описаний отсутствия Save endpoint, decoding в repository и `ST_AsGeoJSON` зарегистрирована post-ingest correction в `FU-2026-10-11-001`.
- Два вопроса metadata/fixture требуют сверки с geometry policy, eligible `L-003` и [артефактами Sprint 2](../docs/sprint_2/README.md), а не нового выбора без изучения кода. Учебный эталон SIM-EVID-001 не является evidence для L-003: first-save остаётся UNVERIFIED. Публичный Save/readback описан, frontend Save/Revert и S2-X01 этим ingest не проверены.
- Обычный `/ingest` без параметров после обработки экспертного research сейчас не нужен: новых RAW inputs нет.
- Проверять модель через интернет-источники и воспроизводимые сценарии; реальные интервью не являются условием эксперимента. Синхронизация legacy requirements/API docs и конфликт lint с неизменяемыми RAW остаются отдельными задачами.
- После persisted edit slice нужен отдельный integrated review/post implementation contract: `ReviewPackage`, reviewer decision, computed `can_post`, simulated post и durable audit.

## Следующее Действие

Отдельной задачей сопоставить принятые решения с S2-X01 и спроектировать недостающие evaluator/restart/архив/доступ по FU-2026-10-13-004. Доменные решения не требуют повторного утверждения вымышленными сотрудниками; текущие guards и границы реализации сохранены.

По `FU-2026-10-11-001` выполнить содержательную сверку: дополнить недостающее техническое знание о registry/replay и истории событий через `/ingest repository-change`, затем исправить зарегистрированные устаревшие описания и сверить доменную очередь с Sprint 2. Для S2-X01 проверить оставшиеся UI-зависимости с учётом уже описанного API/readback; календарные дни не переназначены.
