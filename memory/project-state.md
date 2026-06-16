---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-16
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Состояние Pipeline

- Последний `/discover`: 2026-06-14, совместная 45-минутная сессия `Utility GIS editor` и `Reviewer` спроектировала для следующего релиза risk-tiered routing `geometry/association conflict`; текущий Release 1 не меняется.
- Последний `/ingest`: 2026-06-16, `RAW_inputs/meetings/Reviwer Decision.md` обработан как design/architecture input для Release 2 Reviewer decision; approval of change package for post readiness отделен от technical `post authorization`, trace-boundary conflict закрыт для planned policy.
- Последний `/sync-vision`: 2026-06-16 20:36 +05:00, корневой индекс и live state синхронизированы после двух repository-change ingest; новых RAW inputs и stale-нод нет.
- Последний `/lint-wiki`: 2026-06-16, найдены ожидаемые `missing_frontmatter` для 19 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний `/ingest repository-change`: 2026-06-16, существующие ноды
  `Code_wiki` синхронизированы с package boundaries `utility_service`,
  Docker/CI contract `utility_service` и новой раскладкой backend tests.
- `/ingest repository-change` применяется только если завершённая работа
  содержит новое устойчивое техническое знание для `Code_wiki`. Сам ingest
  определяет нужные ноды, создаёт или обновляет их и пишет компактный реестр;
  завершение плана или commit не являются триггерами.

## Состояние Wiki На 2026-06-16

- Необработанные RAW inputs: не обнаружены; все 20 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs с прошлого `/sync-vision`: не обнаружены.
- Новые значимые Vision ноды с прошлого `/sync-vision`: добавлена summary-нода [[../Vision_wiki/chats/2026-06-16-release-2-reviewer-decision]], обновлены Release 2 reviewer decision/routing, reviewer persona, risk log и follow-up queue.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: новых нод нет; существующие ноды обновлены через repository-change ingest для utility schema/read-only feeder API и package boundaries `utility_service`.
- Stale-ноды: не обнаружены.
- Unresolved conflicts/follow-up items: process conflict `FU-2026-06-01-004` на 19 RAW Markdown files, product validation conflict `FU-2026-06-13-002` и Release 2 user validation `FU-2026-06-14-001`.
- Открытые follow-up'ы: 12.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Интервью с реальным `Utility GIS editor` пока не проведено; checklist находится в `Vision_wiki/chats/2026-06-12-utility-gis-editor-user-interview-checklist.md`.
- Реальное интервью с `Reviewer` по `Vision_wiki/chats/2026-06-13-utility-gis-reviewer-user-interview-checklist.md` пока не проведено; обработанный reviewer source является только синтетической репетицией.
- Нужно внешне проверить, выполняет ли reviewer `post`, требуется ли routing очереди по специализации и допустимо ли совмещение ролей для low-risk changes.
- Broad-domain applicability к electric/water/gas/telecom остается гипотезой; Release 1 сохраняет electric `synthetic_utility_feeder_01`.
- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- После готового read-only feeder API следующий scope Спринта 1: assigned work orders, edit version и frontend shell.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset script, demo сценарий, troubleshooting, `PostGIS seed`, `auth`.
- Нужно реализовать audit/reset contract: audit переживает restart и обычный reset; `full-clean` удаляет всё; обязательны healthcheck, logs, correlation ID и понятные UI errors.
- Нужно выполнить repeatable benchmark P50/P95 для draft performance targets на reference hardware.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
- Для следующего релиза нужно проверить с реальными участниками каноническую planned модель: reviewer decision как package approval for post readiness, разделение `approve package` / technical `post authorization`, routing по affected network area/компетенции/risk tier, `High` через финальное решение `Reviewer`, audit + sample review для безопасного `Normal`, SLA, emergency path и роль Data Owner; текущий Release 1 не расширять.
- Для Release 2 нужно проверить consequence-first `Conflict explanation`: geometry/association diff, validation/dirty areas, trace before/after, affected service/subnetwork, evidence, stale approval, audit и post blockers.
- До implementation contract нужно превратить Release 2 reviewer decision policy в state machine, API/events и audit schema.
- `Operational Utility GIS` хранится только как справочная карта рынка; vendor claims до внешнего использования требуют проверки.
- Нужно снять manual baseline на 10-20 work orders и затем провести 200-work-order product evaluation с 7-дневным correction window.
- Нужно синхронизировать старые generic requirements/API docs с активным utility workflow.
