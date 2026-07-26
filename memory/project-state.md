---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-07-26
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущая доменная модель строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Живое Состояние Pipeline

- Канонический доменный слой: `Wiki/` и `DDD_Wiki/`; `Vision_wiki` остается legacy/source слоем, `Code_wiki` хранит устойчивое техническое знание.
- Ближайший доменный инкремент уточнен: persisted edit slice в `WorkOrder` / `EditVersion` через `UpdateEditVersionFeatureGeometry` для одной line feature и одной внутренней вершины, единое базовое состояние работы, canonical single-vertex precision, AOI `CoveredBy`, atomic guards, `DraftVersionToken`, обязательный `CommandId`, before/after evidence, command response + durable readback и revert. Review/post идет только после устойчивого change set.
- Последний RAW ingest: 2026-07-26, `RAW_inputs/meetings/tolerance_rules.md`.
- Последний `/ingest repository-change`: 2026-07-09, raw SQL workspace aggregate и index hardening working-copy таблиц.
- Последний `/sync-vision`: 2026-07-25 15:53 +05:00.

## Состояние Wiki На 2026-07-26

- RAW inputs: 37 файлов, все отражены в `RAW_inputs/index.md`; новых и необработанных RAW inputs нет.
- Новые `concept` / `decision` / `entity` / `solution` ноды после предыдущего `/sync-vision`: 0.
- `Wiki/_registry` соответствует активным нодам; две superseded-ноды остаются вне активных реестров намеренно.
- Открытые follow-up'ы: 17; полный список — [[../Vision_wiki/decisions/followups/index]].
- Активные blocking conflicts в каноническом `Wiki`: 0. Legacy conflict [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] остается active до docs-синхронизации `FU-2026-06-11-002`.
- Stale-ноды: 0. Доменный тег policy `Stale Approval` нормализован в `stale-approval`, чтобы не смешивать его с признаком устаревшей ноды.
- Последний lint: 2026-07-26. Обнаружены только 36 ожидаемых `missing_frontmatter` в неизменяемых RAW Markdown files, включая новый источник; новых lint-проблем вне `RAW_inputs/` нет. Follow-up `FU-2026-06-01-004` остается открытым.

## Требует Внимания

- После последнего repository-change ingest накопились семь коммитов с устойчивыми техническими изменениями: typed `AuthUser`, workspace details UI, correlation ID и actionable errors, reusable UI controls и восстановление выбранного `WorkOrder` после reload. `Code_wiki` требует отдельного `/ingest repository-change`.
- First-save model имеет один неблокирующий implementation follow-up с двумя оставшимися выборами: фактическая specification/grid demo dataset и точный idempotency window/storage. Fingerprint `CommandId`, baseline mapping и event evidence уже определены.
- Обычный `/ingest` без параметров сейчас не нужен: новых RAW inputs нет.
- Нужны реальные интервью с `Utility GIS editor` и `Reviewer`, синхронизация legacy requirements/API docs и решение конфликта `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- После persisted edit slice нужен отдельный integrated review/post implementation contract: `ReviewPackage`, reviewer decision, computed `can_post`, simulated post и durable audit.

## Следующее Действие

Запустить `/ingest repository-change` для изменений 2026-07-10 — 2026-07-25, затем повторить `/sync-vision`.
