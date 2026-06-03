---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-03
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-03, подготовлена Ф3 по альтернативам и контексту использования для `Utility GIS editor`; затем обработан отдельный RAW deep research report.
- Последний `/ingest`: 2026-06-03, batch RAW ingest `RAW_inputs/documents/03.06.2026deep-research-report.md`; Ф3 сравнила альтернативы для utility authoritative editing.
- Последний `/sync-vision`: 2026-06-03 19:21 +05:00, подтверждены актуальность индексов, отсутствие новых RAW inputs и отсутствие stale-нод после выбора `Utility GIS editor`.
- Последний `/lint-wiki`: 2026-06-03, найдены ожидаемые `missing_frontmatter` для `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`; RAW sources оставлены неизменными по правилу `/ingest`, открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-02, зафиксирован выбор `Utility GIS editor` как primary research-persona, закрытие Ф2 на уровне гипотез и synthetic validation follow-up.

## Изменения С Прошлого `/sync-vision`

- Второй проход `/discover --phase Ф2` выбрал `Utility GIS editor` как primary research-persona, описал work order workflow, reviewer перед post и synthetic validation; все утверждения остаются research-гипотезами.
- `/ingest repository-change` зафиксировал выбор `Utility GIS editor`, закрытие Ф2 на уровне гипотез и synthetic validation follow-up.
- Обработан новый RAW source `RAW_inputs/documents/03.06.2026deep-research-report.md`: baseline `ArcGIS Enterprise + Utility Network`, good-enough alternatives, demo-сценарий и URL follow-up'ы.
- Подтвержден unresolved process conflict: `lint-wiki.py` требует YAML frontmatter от неизменяемых RAW Markdown.
- Корневой `index.md` обновлен строкой текущего `/sync-vision`.

## Состояние Wiki На 2026-06-03

- Новые RAW inputs: 0 необработанных содержательных файлов; `RAW_inputs/documents/03.06.2026deep-research-report.md` обработан 2026-06-03 как Ф3 research.
- Новые значимые Vision ноды с прошлого `/sync-vision`: 1 chat-нода Ф3 и обновленные alternatives, Lean Canvas, Product Vision Board, Risk And Assumption Log и follow-up queue.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на двух RAW Markdown файлах.
- Открытые follow-up'ы: 7.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Для `Utility GIS editor` нужно подготовить synthetic utility dataset; главный Ф3 demo-сценарий - `geometry/association conflict` с dirty areas, network consequence, reviewer decision и authoritative post.
- Нужно пройти Ф4: решить, остается ли GeoService focused conflict/review layer или проверяет более широкий branch/versioning workflow.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно превратить критерий первого релиза "все типа работает" в проверяемый demo-script и acceptance criteria.
