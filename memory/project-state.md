---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-05
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-05, Ф5 business/rollout; выбран local Docker Compose demo для разработчика, decision maker - владелец pet-проекта, ценность - `learning value`, главный rollout-риск - непонятный UI conflict review.
- Последний `/ingest`: 2026-06-05, batch RAW ingest `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; уточнен end-to-end walking skeleton и concrete dataset `synthetic_utility_feeder_01`.
- Последний `/sync-vision`: 2026-06-05 16:57 +05:00, подтверждены актуальность индексов после ingest walking skeleton/dataset, отсутствие новых необработанных RAW inputs и отсутствие stale-нод.
- Последний `/lint-wiki`: 2026-06-05, найдены ожидаемые `missing_frontmatter` для `RAW_inputs/documents/Ф2.md`, `RAW_inputs/documents/03.06.2026deep-research-report.md`, `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` и `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; RAW sources оставлены неизменными по правилу `/ingest`, открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-05, зафиксированы latest RAW ingest walking skeleton/dataset, `/sync-vision` и Ф5 rollout: local Docker Compose developer demo, `learning value`, constraints и conflict review UI risk.

## Изменения С Прошлого `/sync-vision`

- После прошлого `/sync-vision` пройден `/discover --phase Ф4`: приоритет результата - demo; главный сигнал - `review стал проще`; текущий scope - focused conflict/review layer, а full branch versioning/topology/offline/CRDT/rich ACL/production utility network model явно не входят.
- Обработаны RAW sources `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` и `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md` для Ф4 walking skeleton, acceptance criteria и dataset; исходные RAW файлы не редактировались.
- `Vision_wiki/index.md`, `RAW_inputs/index.md`, follow-up queue и solution-ноды уже отражают latest ingest; текущий `/sync-vision` обновил корневое состояние и подтвердил отсутствие новых необработанных источников.
- Подтвержден unresolved process conflict: `lint-wiki.py` требует YAML frontmatter от неизменяемых RAW Markdown.
- Корневой `index.md` обновлен строкой текущего `/sync-vision` от 2026-06-05.
- После sync пройден `/discover --phase Ф5`: rollout - локальное demo; audience - developer; первый flow - `Editor`; нужны README, seed/reset script, demo сценарий и troubleshooting; external GIS и `ArcGIS`/`QGIS` export не входят.

## Состояние Wiki На 2026-06-05

- Необработанные RAW inputs: не обнаружены.
- Новые значимые Vision ноды с прошлого `/sync-vision`: Ф4 chat-нода, source summary-нода 2026-06-05, Ф5 rollout chat-нода, constraints-нода и обновленные USM, roadmap, architecture vision, Lean Canvas, Risk And Assumption Log и follow-up queue.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на четырех RAW Markdown files, включая `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`.
- Открытые follow-up'ы: 6.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Для `Utility GIS editor` нужно реализовать/подготовить `synthetic_utility_feeder_01`: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions, 4 conflict-сценария.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset script, demo сценарий, troubleshooting, `PostGIS seed`, `auth`.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
