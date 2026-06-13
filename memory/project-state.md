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

- Последний `/discover`: 2026-06-12, подготовлено 30-минутное интервью с реальным `Utility GIS editor` для проверки фактического workflow и пользовательской боли на последнем реальном work order.
- Последний `/ingest`: 2026-06-12, обработан `RAW_inputs/meetings/utility_gis_editor_answers.md` как синтетическая репетиция; persona и JTBD приняты для design, но external user validation не заявляется.
- Последний `/sync-vision`: 2026-06-12 15:14 +05:00, индексы и live state синхронизированы после Ф8, code compliance, планирования Release 1 и контрактов Дня 1 Спринта 1; новых необработанных RAW inputs и stale-нод нет.
- Последний `/lint-wiki`: 2026-06-13, найдены ожидаемые `missing_frontmatter` для 12 неизменяемых RAW Markdown files; открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-13, реализованы роли и доступ
  Дня 2: `Editor`/`Reviewer`, DB-backed auth, stable demo seed, realtime policy,
  Reviewer placeholder и подтверждённая совместимость CI/Docker Compose.

## Изменения С Прошлого `/sync-vision`

- Ф8 приняла новый Release 1: work order -> edit version -> validation -> reconcile -> conflict resolution -> review -> post -> audit.
- Добавлены Ф8 chat-нода, решение `release_1_utility_workflow`, resolved conflict старого и нового scope, design spec и follow-up'ы на code compliance matrix и синхронизацию старых requirements.
- Составлена code compliance matrix; `FU-2026-06-11-001` закрыт.
- Реализация разбита на 7 двухнедельных спринтов крупного уровня: foundation, editing, validation, reconcile, review/post, audit/demo operations, acceptance/hardening. Детальная техническая декомпозиция выполняется отдельно перед каждым спринтом.
- Спринт 1 разложен на 14 календарных дней: будние дни интенсивные, выходные облегченные для интеграции, документации и резерва; итоговый путь - login -> assigned work order -> create/open edit version -> workspace.
- День 1 является контрактным: AC-01..AC-07, сущности и инварианты, endpoints/DTO/errors и backlog S1-01..S1-10 согласованы; документы находятся в `docs/sprint_1`.
- День 2 реализовал строгие взаимоисключающие роли `Editor`/`Reviewer`,
  удаление legacy `Viewer`, DB-backed active-user auth, stable demo users
  `alexey.editor`, `bolat.editor`, `marina.reviewer`, read-only realtime для
  обеих ролей и отдельный Reviewer placeholder.
- Migration `b82a5f2d91c3` и существующая seed-цепочка проверены на upgrade
  сохранённого legacy volume и на clean install. Reviewer queue, assignment
  authorization, approve/reject и `post` остаются в следующих backlog items.
- Реализация плана Дня 2 должна выполняться в текущей ветке без worktree,
  `git add` и `git commit`; существующий staging пользователя нельзя менять.
  Demo users создаются через `seed_demo_users.py`, `run_demo_user_seed()` и
  `DemoUserSeedService`, без нового параллельного seed-механизма.
- Все текущие jobs `.github/workflows/ci.yml`, backend/frontend Docker builds
  и Compose-сценарии `backend`, `dev`, `prod` являются обязательными
  regression gates Дня 2. Backend `63 passed`, frontend `29 passed`; clean
  install, upgrade legacy volume, base CI smoke и профили `dev`/`prod`
  подтверждены. Отдельного CD workflow сейчас нет.
- `AOI` принят как серверная граница данных workspace, `Feeder` - как агрегат `NetworkFeature` и внутрефидерных `NetworkAssociation`; пользовательский текст и application logs должны быть на русском языке.
- Новых RAW inputs с прошлого sync нет; все 12 источников остаются отражены в `RAW_inputs/index.md`.
- Новых concept/decision/entity/solution нод с прошлого sync: concept - 0, decision - 2, entity - 0, solution - 0.
- Известный process conflict `FU-2026-06-01-004` по 12 неизменяемым RAW Markdown files остается актуальным.
- Синтетическая репетиция поддержала utility workflow и выявила дополнительную зону ценности: единый evidence context для work order, документов, changes, validation/trace, conflicts и review.

## Состояние Wiki На 2026-06-12

- Необработанные RAW inputs: не обнаружены; все 13 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs с прошлого `/sync-vision`: 1, синтетическая репетиция интервью обработана.
- Новые значимые Vision ноды с прошлого `/sync-vision`: Ф8 chat-нода, active decision `release_1_utility_workflow` и resolved conflict старого generic scope с utility workflow.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: отдельных нод нет; обновлены `Code_wiki/index.md` и журнал `repository_change_ingest.md`, добавлены связанные compliance и Sprint 1 документы.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`; сейчас проявляется на 12 RAW Markdown files.
- Открытые follow-up'ы: 10.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Реальных пользователей пока нет; внешний workflow/conflict UX test по `Vision_wiki/chats/2026-06-12-utility-gis-editor-user-interview-checklist.md` отложен до появления доступа к представителям роли.
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
