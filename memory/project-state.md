---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-10-12
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущая доменная модель строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Живое Состояние Pipeline

- Канонический доменный слой: `Wiki/` и `DDD_Wiki/`; `Vision_wiki` остается legacy/source слоем, `Code_wiki` хранит устойчивое техническое знание.
- Ближайший доменный инкремент уточнен: persisted edit slice в `WorkOrder` / `EditVersion` через `UpdateEditVersionFeatureGeometry` для одной line feature и одной внутренней вершины, единое базовое состояние работы, server-side canonicalization по actual dataset metadata, AOI `CoveredBy`, atomic guards, явный `POSITIONAL_ACCURACY_UNVERIFIED`, `DraftVersionToken`, lifecycle-safe `CommandId`, before/after evidence, command response + durable readback и revert. Review/post требует verified positional acceptance после устойчивого change set.
- Последний RAW ingest: 2026-10-11, `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md`; 15 синтезированных ответов заказчика, правила приняты пользователем 2026-10-12.
- Последний `/ingest repository-change` по реестру: 2026-10-10, `EditVersionRepository` и transaction-bound persistence; перед ним учтена deterministic geometry от 2026-10-08.
- Последний `/sync-vision`: 2026-10-11 22:07 +05:00.

## Состояние Wiki На 2026-10-12

- RAW inputs: 39 файлов, все отражены в `RAW_inputs/index.md`; новых и необработанных RAW inputs нет.
- Новые `concept` / `decision` / `entity` / `solution` ноды после предыдущего `/sync-vision`: 0; добавлены 2 `technical-note` в `Code_wiki`: [[../Code_wiki/архитектура/edit_geometry_determinism]] и [[../Code_wiki/архитектура/edit_version_persistence]].
- `Wiki/_registry` соответствует активным нодам; две superseded-ноды остаются вне активных реестров намеренно.
- Открытые follow-up'ы: 19; полный список — [[../Vision_wiki/decisions/followups/index]]. В [[../Wiki/_registry/questions]] остаются 5 открытых вопросов.
- Активные blocking conflicts в каноническом `Wiki`: 0; [[../Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]] разрешён решением пользователя 2026-10-12. Legacy conflict [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] остается active до docs-синхронизации `FU-2026-06-11-002`.
- Stale-ноды: 3 — [[../Code_wiki/архитектура/backend]], [[../Code_wiki/архитектура/edit_version_persistence]] и [[../DDD_Wiki/model_health]]. Причина — отставание описания Save service и очереди fixture/metadata от текущего кода и Sprint 2; см. `FU-2026-10-11-001`.
- Последняя проверка `lint-wiki.py`: 2026-10-11 в рамках `/sync-vision`. Обнаружены только 37 ожидаемых `missing_frontmatter` в неизменяемых RAW Markdown files; проблем вне `RAW_inputs/` нет. Последний ранее зафиксированный lint — 2026-07-31. Follow-up `FU-2026-06-01-004` остается открытым.

## Требует Внимания

- Принятые правила восстановления, языка качества и D5-Q1 отражены в отдельной [S2-X01](../docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md), вне дней, статус «запланировано». Actual positional specification/допуск, срок history и реальные ответственные остаются открыты (`FU-2026-10-11-003`).

- `Code_wiki` частично синхронизирован в октябре, но внутренний backend Save/Revert, registry/replay, terminal rejection и события от 2026-10-11 требуют отдельного `/ingest repository-change`. Также нужна проверка покрытия июльских frontend-изменений и более поздних fixtures/schema/history; сам факт октябрьского ingest не подтверждает их полноту.
- First-save вопросы о positional acceptance, metadata, fixture и retention остаются открыты в реестре. Перед новым discovery сверить их с geometry policy, eligible `L-003` и принятыми [артефактами Sprint 2](../docs/sprint_2/README.md); не повторять вопрос о выборе fixture без этой сверки. Готовность публичного Save API/UI текущим `/sync-vision` не оценивалась.
- Обычный `/ingest` без параметров после обработки research о восстановлении сейчас не нужен: новых RAW inputs нет.
- Нужны реальные интервью с `Utility GIS editor` и `Reviewer`, синхронизация legacy requirements/API docs и решение конфликта `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- После persisted edit slice нужен отдельный integrated review/post implementation contract: `ReviewPackage`, reviewer decision, computed `can_post`, simulated post и durable audit.

## Следующее Действие

Выполнить S2-X01 после появления базовых API/readback/UI зависимостей; календарные дни не переназначены. Отдельно остаются `/ingest repository-change` для знания о Save/Revert и истории событий, сверка доменной очереди с принятыми Sprint 2 источниками по `FU-2026-10-11-001` и последующий `/sync-vision`.
