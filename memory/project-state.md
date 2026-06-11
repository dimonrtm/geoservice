---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-11
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-11, Ф8 closeout; Release 1 пересобран вокруг полного `Utility GIS editor` workflow, generic GIS оставлен внутренним foundation.
- Последний `/ingest`: 2026-06-11, repository-change по планированию нового Release 1; зафиксированы code compliance matrix и план из 7 двухнедельных спринтов.
- Последний `/sync-vision`: 2026-06-11 17:59 +05:00, подтверждены актуальность индексов после Ф7 и repository-change ingest, отсутствие новых необработанных RAW inputs и отсутствие stale-нод.
- Последний `/lint-wiki`: 2026-06-11, найдены ожидаемые `missing_frontmatter` для 11 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-11, зафиксированы новый Release 1, code compliance matrix и крупноуровневый план из 7 спринтов.

## Изменения С Прошлого `/sync-vision`

- Пройдена Ф7: создан `Vision_wiki/concepts/metrics.md`, приняты North Star/guardrails, risk register и порядок workflow -> validation -> conflict experiments.
- Пять RAW sources Ф7 использованы для метрик, post-problem taxonomy, manual baseline и risky assumptions.
- Обновлены `nfr.md`, `roadmap.md`, `risk_assumption_log.md` и follow-up queue; открыты measurement pipeline и manual baseline follow-up'ы.
- Выполнен repository-change ingest по результатам Ф7.
- Новых concept/decision/entity/solution нод с прошлого sync: concept - 1, decision - 0, entity - 0, solution - 0.
- Известный process conflict `FU-2026-06-01-004` по 11 неизменяемым RAW Markdown files остается актуальным.
- Ф8 приняла новый Release 1: work order -> edit version -> validation -> reconcile -> conflict resolution -> review -> post -> audit.
- Добавлены решение `release_1_utility_workflow`, design spec и follow-up'ы на code compliance matrix и синхронизацию старых requirements.
- Составлена code compliance matrix; `FU-2026-06-11-001` закрыт.
- Реализация разбита на 7 двухнедельных спринтов крупного уровня: foundation, editing, validation, reconcile, review/post, audit/demo operations, acceptance/hardening. Детальная техническая декомпозиция выполняется отдельно перед каждым спринтом.

## Состояние Wiki На 2026-06-11

- Необработанные RAW inputs: не обнаружены; все 12 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs с прошлого `/sync-vision`: 5, все использованы в Ф7.
- Новые значимые Vision ноды с прошлого `/sync-vision`: Ф7 chat-нода и concept `metrics`.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет; обновлен журнал `repository_change_ingest.md`.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на 11 RAW Markdown files.
- Открытые follow-up'ы: 10.

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
- Нужно выполнить Спринт 1: utility schema, роли/seed, assigned work orders, edit version и frontend shell.
- Нужно синхронизировать старые generic requirements/API docs с активным utility workflow.
