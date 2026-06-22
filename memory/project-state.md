---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-22
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Состояние Pipeline

- Последний `/discover`: 2026-06-22, Ф5 по `geometry/association conflict` сузила Release 2 rollout до internal developer demo: decision maker, first user и budget owner - `разработчик demo`; следующий артефакт - `implementation contract`.
- Последний `/ingest`: 2026-06-22, `RAW_inputs/meetings/geometry_association_conflict_f5.md` обработан как Ф5 research/design input для Release 2; уточнены value signal, workflow placement after reconcile, rollout roles, required integrations, non-goals, false-confidence risk, support package, acceptable claims и first rollout scenario.
- Последний `/sync-vision`: 2026-06-22 18:08 +05:00, корневой индекс, `Code_wiki/index.md` и live state синхронизированы после repository-change ingest 2026-06-21/22; новых RAW inputs и stale-нод нет.
- Последний `/lint-wiki`: 2026-06-22, через bundled Python найдены ожидаемые `missing_frontmatter` для 25 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний `/ingest repository-change`: 2026-06-22, существующие ноды
  `Code_wiki` синхронизированы с переносом AOI в `work_order`, nested
  Workspace API `/api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`,
  отсутствием AOI в Utility Network API, seed ownership через `SeedWorkOrderRepository`
  и repair/idempotent migration contract для schema-boundary откатов.
- `/ingest repository-change` применяется только если завершённая работа
  содержит новое устойчивое техническое знание для `Code_wiki`. Сам ingest
  определяет нужные ноды, создаёт или обновляет их и пишет компактный реестр;
  завершение плана или commit не являются триггерами.

## Состояние Wiki На 2026-06-22

- Необработанные RAW inputs: не обнаружены; все 26 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs с прошлого `/sync-vision`: не обнаружены.
- Новые значимые Vision ноды с прошлого `/sync-vision`: [[../Vision_wiki/chats/2026-06-22-geometry-association-conflict-f5]].
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: новых нод нет; обновлены существующие ноды [[../Code_wiki/архитектура/data_model]], [[../Code_wiki/архитектура/api_and_realtime]] и [[../Code_wiki/состояние_проекта/repository_change_ingest]] после repository-change ingest 2026-06-21/22.
- Stale-ноды: не обнаружены.
- Unresolved conflicts/follow-up items: process conflict `FU-2026-06-01-004` на 24 RAW Markdown files, product validation `FU-2026-06-13-002` и Release 2 user validation `FU-2026-06-14-001`; conflict-нода [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] остается active как documented boundary до docs-синхронизации `FU-2026-06-11-002`.
- Открытые follow-up'ы: 12.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Интервью с реальным `Utility GIS editor` пока не проведено; checklist находится в `Vision_wiki/chats/2026-06-12-utility-gis-editor-user-interview-checklist.md`.
- Реальное интервью с `Reviewer` по `Vision_wiki/chats/2026-06-13-utility-gis-reviewer-user-interview-checklist.md` пока не проведено; обработанный reviewer source является только синтетической репетицией.
- Нужно внешне проверить, выполняет ли reviewer `post`, требуется ли routing очереди по специализации и допустимо ли совмещение ролей для low-risk changes.
- Broad-domain applicability к electric/water/gas/telecom остается гипотезой; Release 1 сохраняет electric `synthetic_utility_feeder_01`.
- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Нужно добавить доступные URL для non-Esri vendor-specific утверждений из `RAW_inputs/documents/Ф2.md` и `RAW_inputs/documents/03.06.2026deep-research-report.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset script, demo сценарий, troubleshooting, `PostGIS seed`, `auth`.
- Нужно продолжить Спринт 1 после готовых roles/access, utility schema, `synthetic_utility_feeder_01`, read-only feeder API, `WorkOrder` и создания `EditVersion` из per-WorkOrder `DefaultState`; следующий scope - frontend shell и дальнейшие шаги workflow.
- Нужно реализовать audit/reset contract: audit переживает restart и обычный reset; `full-clean` удаляет всё; обязательны healthcheck, logs, correlation ID и понятные UI errors.
- Нужно выполнить repeatable benchmark P50/P95 для draft performance targets на reference hardware.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
- Для следующего релиза нужно проверить с реальными участниками каноническую planned модель: reviewer decision как package approval for post readiness, разделение `approve package` / technical `post authorization`, routing по affected network area/компетенции/risk tier, `High` через финальное решение `Reviewer`, audit + sample review для безопасного `Normal`, SLA, emergency path и роль Data Owner; текущий Release 1 не расширять.
- Для Release 2 нужно проверить consequence-first `Conflict explanation`: primary user `Editor`, geometry/association diff, validation/dirty areas, trace before/after, affected service/subnetwork, evidence, stale approval, audit и post blockers; отдельно проверить, снижает ли он внешние проверки и time-to-confident-decision и не дублирует ли обычный Conflicts view.
- Для Release 2 Ф4 demo нужно проверить canonical transformer terminal association scenario, read-only consequence package, `Normal/High/Critical` без преждевременного `Simple`, stale/failure case и audit object.
- Нужно проверить с реальными представителями роли, подтверждается ли описание `Utility GIS editor` как owner/editor of authoritative utility network changes, включая topology QA, version governance, field/office sync, import cleanup и operational integrations.
- Для Release 2 нужно сравнить unified evidence context против `ArcGIS native + SOP + expert handoff` и custom internal overlay: измерить внешние trace/check opens, notes/screenshots, handoff и time-to-confident-decision.
- До implementation contract нужно превратить Release 2 reviewer decision policy и Ф4 consequence package в state machine, API/events, audit schema и demo fixtures.
- Ф5 rollout подтвердил, что следующий шаг по Release 2 `geometry/association conflict` - именно `implementation contract` для developer demo, а не commercial/on-prem go-to-market.
- `Operational Utility GIS` хранится только как справочная карта рынка; vendor claims до внешнего использования требуют проверки.
- Нужно снять manual baseline на 10-20 work orders и затем провести 200-work-order product evaluation с 7-дневным correction window.
- Нужно синхронизировать старые generic requirements/API docs с активным utility workflow.
