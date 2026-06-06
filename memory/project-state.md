---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-06
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-06, Ф6 constraints/NFR; зафиксированы reference hardware, Chrome, startup/reset за несколько минут, JWT, несовместимые роли `Editor`/`Reviewer`, audit persistence, observability minimum и включение `import GeoJSON`.
- Последний `/ingest`: 2026-06-06, batch RAW ingest `RAW_inputs/documents/utility_gis_editor_target_times.md`; добавлены draft P95 targets для map/edit/validation/reconcile/conflict/post и benchmark follow-up.
- Последний `/sync-vision`: 2026-06-06 10:21 +05:00, подтверждены актуальность индексов после Ф5 и repository-change ingest, отсутствие новых необработанных RAW inputs и отсутствие stale-нод.
- Последний `/lint-wiki`: 2026-06-06, найдены ожидаемые `missing_frontmatter` для `RAW_inputs/documents/Ф2.md`, `RAW_inputs/documents/03.06.2026deep-research-report.md`, `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` и `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; RAW sources оставлены неизменными по правилу `/ingest`, открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-06, зафиксирована Ф6: local demo NFR, JWT roles, audit/reset contract, observability minimum и включение `import GeoJSON`.

## Изменения С Прошлого `/sync-vision`

- Пройден `/discover --phase Ф5`: rollout - local Docker Compose demo; audience - developer; decision maker - владелец pet-проекта; первый flow - `Editor`; ценность - `learning value`.
- Добавлены Ф5 chat-нода и `Vision_wiki/decisions/constraints.md`; обновлены Lean Canvas, roadmap, Risk And Assumption Log и follow-up queue.
- Добавлены `FU-2026-06-05-001` для local demo support package и `FU-2026-06-05-002` для проверки UI conflict review.
- Выполнен `/ingest repository-change`, который зафиксировал Ф5 rollout и актуальное состояние knowledge wiki в `Code_wiki/состояние_проекта/repository_change_ingest.md`.
- Подтвержден unresolved process conflict: `lint-wiki.py` требует YAML frontmatter от четырех неизменяемых RAW Markdown files.
- Корневой `index.md` обновлен строкой текущего `/sync-vision` от 2026-06-06.
- После sync пройден `/discover --phase Ф6`: обычный restart сохраняет данные, обычный reset восстанавливает seed и сохраняет audit, а отдельный `full-clean` очищает demo data и audit.
- Обработан RAW source с performance targets; NFR теперь содержит измеримые draft P95 thresholds, которые требуют проверки на reference hardware.

## Состояние Wiki На 2026-06-06

- Необработанные RAW inputs: не обнаружены после ingest `utility_gis_editor_target_times.md`.
- Новые значимые Vision ноды с прошлого `/sync-vision`: Ф5 rollout chat-нода, constraints-нода и Ф6 NFR chat-нода; обновлены NFR, architecture vision, roadmap, Risk And Assumption Log и follow-up queue.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет; обновлен существующий журнал `repository_change_ingest.md`.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на пяти RAW Markdown files, включая `RAW_inputs/documents/utility_gis_editor_target_times.md`.
- Открытые follow-up'ы: 7.

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
