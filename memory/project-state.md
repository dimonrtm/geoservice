---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-07
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-07, Ф7 metrics/risks; зафиксированы `Safe Authoritative Post Rate >=95%` на 200 work orders, 7-дневное correction window, safety blockers, manual baseline и минимальные эксперименты.
- Последний `/ingest`: 2026-06-07, batch RAW ingest `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`; добавлены domain concept, source summary и desired utility vocabulary без расширения demo-scope.
- Последний `/sync-vision`: 2026-06-07 10:58 +05:00, подтверждены актуальность индексов после Ф6 и двух RAW ingest, отсутствие новых необработанных RAW inputs и отсутствие stale-нод.
- Последний `/lint-wiki`: 2026-06-07, найдены ожидаемые `missing_frontmatter` для 11 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-07, зафиксирована Ф7: North Star, safety gates, manual baseline, performance classification и validation experiments.

## Изменения С Прошлого `/sync-vision`

- Пройден `/discover --phase Ф6`: зафиксированы reference hardware, Chrome, JWT, separation of duties, audit/reset contract, observability minimum и включение `import GeoJSON`.
- Обработаны два новых RAW source: `utility_gis_editor_target_times.md` и `utility_gis_editor_domain_dictionary.md`.
- Добавлены draft P95 targets и `FU-2026-06-06-001` для repeatable benchmark.
- Созданы summary словаря домена и concept `utility_gis_editing_domain`; `technical_terms.md` дополнен desired utility demo vocabulary.
- Новых concept/decision/entity/solution нод с прошлого sync: concept - 1, decision - 0, entity - 0, solution - 0.
- Известный process conflict `FU-2026-06-01-004` теперь проявляется на 11 неизменяемых RAW Markdown files.
- Пройдена Ф7: создан `Vision_wiki/concepts/metrics.md`, приняты North Star/guardrails, risk register и порядок workflow -> validation -> conflict experiments.
- Пять новых RAW sources Ф7 использованы для метрик, post-problem taxonomy, manual baseline и risky assumptions.

## Состояние Wiki На 2026-06-07

- Необработанные RAW inputs: не обнаружены; пять новых Ф7 sources связаны с metrics/discovery нодами.
- Новые RAW inputs с прошлого `/sync-vision`: 7, все обработаны или использованы в Ф7.
- Новые значимые Vision ноды с прошлого `/sync-vision`: Ф6 chat-нода, performance targets summary, domain dictionary summary и concept `utility_gis_editing_domain`.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет; `technical_terms.md` дополнен desired utility demo vocabulary.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на 11 RAW Markdown files.
- Открытые follow-up'ы: 9.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Для `Utility GIS editor` нужно реализовать/подготовить `synthetic_utility_feeder_01`: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions, 4 conflict-сценария.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset script, demo сценарий, troubleshooting, `PostGIS seed`, `auth`.
- Нужно реализовать audit/reset contract: audit переживает restart и обычный reset; `full-clean` удаляет всё; обязательны healthcheck, logs, correlation ID и понятные UI errors.
- Нужно выполнить repeatable benchmark P50/P95 для draft performance targets на reference hardware.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
- Нужно снять manual baseline на 10-20 work orders и затем провести 200-work-order product evaluation с 7-дневным correction window.
