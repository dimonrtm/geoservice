---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-13
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Состояние Pipeline

- Последний `/discover`: 2026-06-13, подготовлено 30-минутное интервью с реальным `Reviewer` инженерной GIS-сети через разбор последнего review-кейса, evidence, критериев решения, возвратов и публикации.
- Последний `/ingest`: 2026-06-13, обработаны broad-domain synthetic sources `utility_gis_editor_broad_domain_answers.md` и `utility_gis_reviewer_broad_domain_answers.md`; уточнены physical/logical network, as-built/redlining, review package и publisher responsibility без расширения Release 1 scope.
- Последний `/sync-vision`: 2026-06-13 19:03 +05:00, индексы и live state синхронизированы после синтетической репетиции интервью, RBAC Дня 2 Спринта 1 и оптимизации agent memory/knowledge pipeline; необработанных RAW inputs и stale-нод нет.
- Последний `/lint-wiki`: 2026-06-13, найдены ожидаемые `missing_frontmatter` для 15 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний `/ingest repository-change`: 2026-06-13, существующие ноды `Code_wiki` синхронизированы с RBAC Дня 2 и новым workflow agent memory audit.
- `/ingest repository-change` применяется только если завершённая работа
  содержит новое устойчивое техническое знание для `Code_wiki`. Сам ingest
  определяет нужные ноды, создаёт или обновляет их и пишет компактный реестр;
  завершение плана или commit не являются триггерами.

## Состояние Wiki На 2026-06-13

- Необработанные RAW inputs: не обнаружены; все 16 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs с прошлого `/sync-vision`: 4, synthetic editor/reviewer sources и их broad-domain расширения обработаны.
- Новые значимые Vision ноды с прошлого `/sync-vision`: чек-листы реальных интервью, четыре synthetic source summary и design-персона `Utility GIS Reviewer`; обновлены domain concept, personas, JTBD, risk log и follow-up queue.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: отдельных нод нет; существующие architecture, local development, deployment, CI/testing и project-state ноды обновлены по RBAC Дня 2 и memory audit workflow.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: process conflict `FU-2026-06-01-004` на 15 RAW Markdown files и product validation conflict `FU-2026-06-13-002` по границам reviewer role.
- Открытые follow-up'ы: 11.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Интервью с реальным `Utility GIS editor` пока не проведено; checklist находится в `Vision_wiki/chats/2026-06-12-utility-gis-editor-user-interview-checklist.md`.
- Реальное интервью с `Reviewer` по `Vision_wiki/chats/2026-06-13-utility-gis-reviewer-user-interview-checklist.md` пока не проведено; обработанный reviewer source является только синтетической репетицией.
- Нужно внешне проверить, выполняет ли reviewer `post`, требуется ли routing очереди по специализации и допустимо ли совмещение ролей для low-risk changes.
- Broad-domain applicability к electric/water/gas/telecom остается гипотезой; Release 1 сохраняет electric `synthetic_utility_feeder_01`.
- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Для `Utility GIS editor` нужно реализовать/подготовить `synthetic_utility_feeder_01`: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions, 4 conflict-сценария.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset script, demo сценарий, troubleshooting, `PostGIS seed`, `auth`.
- Нужно реализовать audit/reset contract: audit переживает restart и обычный reset; `full-clean` удаляет всё; обязательны healthcheck, logs, correlation ID и понятные UI errors.
- Нужно выполнить repeatable benchmark P50/P95 для draft performance targets на reference hardware.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
- Нужно снять manual baseline на 10-20 work orders и затем провести 200-work-order product evaluation с 7-дневным correction window.
- Нужно продолжить Спринт 1: utility schema, assigned work orders, edit version
  и frontend shell; роли/seed Дня 2 завершены.
- Нужно синхронизировать старые generic requirements/API docs с активным utility workflow.
