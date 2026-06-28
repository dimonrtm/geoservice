---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-28
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущая доменная модель строится вокруг полного `Utility GIS editor` workflow от назначенного work order и изолированной edit version до validation, reconcile, review, authoritative post и audit.

## Состояние Pipeline

- Доменный слой активирован: `Wiki/` хранит канонические атомарные доменные знания и registry tables, `DDD_Wiki/` хранит DDD-модель и `DDD_Wiki/model_health.md`; `Vision_wiki` остается legacy/source слоем, `Code_wiki` продолжает наполняться через repository ingest.
- `/discover` для непустого проекта должен исследовать текущую доменную модель и конфликты, сгенерировать 150 candidate questions и показать top 15.
- `/plan-sprint` добавлен как workflow планирования 14-дневного спринта на основе текущего кода, `Code_wiki`, `Wiki/DDD_Wiki`, конфликтов и top 15 из 150 planning questions.

- Последний `/discover`: 2026-06-23, подготовлен checklist Ф8 по `geometry/association conflict` для closeout Release 2: ready-to-implement decisions, remaining blockers, RAW artifacts, wiki updates и следующие шаги перед implementation contract.
- Последний `/ingest`: 2026-06-28, `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md` обработан как design/architecture input для first persisted edit slice; уточнено, что следующий sprint должен сначала дать `UpdateEditVersionFeatureGeometry`: geometry diff существующей line feature относительно baseline, readback persisted feature + diff, normalized `operation`, `DraftVersionToken` и basic draft validation flags.
- Последний `/sync-vision`: 2026-06-28 22:01 +05:00, корневой индекс и live state синхронизированы после post-sync commit `b8f0740` / ingest `RAW_inputs/meetings/increment_after_open_workspace.md`; `Wiki/_registry` сверен с фактическими нодами, необработанных RAW inputs и stale-нод не обнаружено.
- Последний `/lint-wiki`: 2026-06-28, через bundled Python найдены ожидаемые `missing_frontmatter` для 32 RAW Markdown files; новых lint-ошибок вне RAW source files не обнаружено, открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний `/ingest repository-change`: 2026-06-26, существующие ноды
  `Code_wiki` синхронизированы с Day 13 full path API smoke: CI запускает
  `tests/smoke/full_path_workspace_smoke.py` внутри `utility_service` и
  проверяет `login -> assigned-to-me -> open/reopen EditVersion -> workspace`
  для seeded `WO-001`; smoke runner живет в `apps/backend/tests/smoke` и
  покрыт focused unit tests.
- `/ingest repository-change` применяется только если завершённая работа
  содержит новое устойчивое техническое знание для `Code_wiki`. Сам ingest
  определяет нужные ноды, создаёт или обновляет их и пишет компактный реестр;
  завершение плана или commit не являются триггерами.

## Состояние Wiki На 2026-06-28

- Необработанные RAW inputs: не обнаружены; все 33 RAW sources отражены в `RAW_inputs/index.md`.
- Новые RAW inputs, учтенные после предыдущего `/sync-vision`: `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; источник обработан через `/ingest`.
- Новые значимые Vision ноды с прошлого `/sync-vision`: [[../Vision_wiki/chats/2026-06-28-persisted-edit-slice-editversion]].
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: новых нод нет; обновлены `Code_wiki/сборка/ci_and_quality.md`, `Code_wiki/правила_и_стиль/testing_strategy.md` и компактный реестр repository-change ingest для Day 13 full path API smoke.
- Новые значимые Wiki/DDD_Wiki ноды с прошлого `/sync-vision`: добавлены [[../Wiki/commands/update_edit_version_feature_geometry]], [[../Wiki/domain_events/edit_version_change_set_persisted]], [[../Wiki/specifications/edit_version_basic_draft_validation]], [[../Wiki/value_objects/draft_version_token]] и [[../DDD_Wiki/invariants/edit_version_persisted_edit_invariants]]; старые generic first-slice узлы [[../Wiki/commands/update_edit_version_feature]] и [[../Wiki/domain_events/edit_version_feature_updated]] помечены superseded; [[../DDD_Wiki/model_health]] уточнен вокруг persisted geometry diff existing line feature.
- Stale-ноды: не обнаружены.
- Unresolved conflicts/follow-up items: process conflict `FU-2026-06-01-004` на 32 RAW Markdown files, product validation `FU-2026-06-13-002`, Release 2/user validation `FU-2026-06-14-001`, review/post implementation contract `FU-2026-06-23-001`, experiment design `FU-2026-06-23-002`, Release 2 real validation checklist `FU-2026-06-23-003` и legacy contract docs cleanup `FU-2026-06-26-001`; canonical `Wiki` conflicts [[../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]], [[../Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]], [[../Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] и [[../Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] resolved новым RAW source; conflict-нода [[../Vision_wiki/decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] остается active как documented boundary до docs-синхронизации `FU-2026-06-11-002`.
- Открытые follow-up'ы: 16.

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
- Нужно продолжить Спринт 1 после готовых roles/access, utility schema, `synthetic_utility_feeder_01`, read-only feeder API, `WorkOrder`, создания `EditVersion` из per-WorkOrder `DefaultState`, экрана `Мои наряды`, Edit Workspace и full path API smoke; следующий scope - persisted edit slice: geometry diff существующей line feature, `UpdateEditVersionFeatureGeometry`, readback persisted feature + diff, normalized `operation`, `DraftVersionToken` и basic draft validation flags.
- Нужно реализовать audit/reset contract: audit переживает restart и обычный reset; `full-clean` удаляет всё; обязательны healthcheck, logs, correlation ID и понятные UI errors.
- Нужно выполнить repeatable benchmark P50/P95 для draft performance targets на reference hardware.
- Нужно спроектировать/проверить понятный UI conflict review для developer demo.
- Для следующего релиза нужно проверить с реальными участниками каноническую planned модель: reviewer decision как package approval for post readiness, разделение `approve package` / technical `post authorization`, routing по affected network area/компетенции/risk tier, `High` через финальное решение `Reviewer`, audit + sample review для безопасного `Normal`, SLA, emergency path и роль Data Owner; текущий Release 1 не расширять.
- Для Release 2 нужно проверить consequence-first `Conflict explanation`: primary user `Editor`, geometry/association diff, validation/dirty areas, trace before/after, affected service/subnetwork, evidence, stale approval, audit и post blockers; отдельно проверить, снижает ли он внешние проверки и time-to-confident-decision и не дублирует ли обычный Conflicts view.
- Для Release 2 Ф4 demo нужно проверить canonical transformer terminal association scenario, read-only consequence package, `Normal/High/Critical` без преждевременного `Simple`, stale/failure case и audit object.
- Нужно проверить с реальными представителями роли, подтверждается ли описание `Utility GIS editor` как owner/editor of authoritative utility network changes, включая topology QA, version governance, field/office sync, import cleanup и operational integrations.
- Для Release 2 нужно сравнить unified evidence context против `ArcGIS native + SOP + expert handoff` и custom internal overlay: измерить внешние trace/check opens, notes/screenshots, handoff, time-to-confident-decision, duplicate-view rate и unclear next step rate.
- Нужно подготовить отдельный integrated review/post implementation contract v0.1 для developer demo после persisted edit slice: `ReviewPackage` как snapshot persisted change set, затем `submit_for_review`, reviewer decision, computed `can_post`, pre-post check, simulated post, durable audit, system `post-gate`, safety-complete veto set, `DefaultChangedAfterReconcile`, zero false-safe gate и small-sprint rollout через существующий `WorkOrder` / `EditVersion` flow.
- Для Release 2 Ф7 нужно подготовить measurement harness: scripted golden walkthrough, 10 deterministic repeats canonical scenario, 10 mutated stale/blocker/pre-post variants, optional 30 automated runs и manual baseline против `ArcGIS native Conflicts view + SOP + expert handoff`.
- Для Release 2 нужно подготовить отдельный real validation checklist для `Editor`/`Reviewer`: risk wording, authority matrix для High/Critical, sample review для `Normal`, evidence sufficiency thresholds, repeat-review UX и trust к blocker verdict.
- Ф5 rollout подтвердил, что следующий шаг по Release 2 `geometry/association conflict` - именно `implementation contract` для developer demo, а не commercial/on-prem go-to-market.
- `Operational Utility GIS` хранится только как справочная карта рынка; vendor claims до внешнего использования требуют проверки.
- Нужно снять manual baseline на 10-20 work orders и затем провести 200-work-order product evaluation с 7-дневным correction window.
- Нужно синхронизировать старые generic requirements/API docs с активным utility workflow.
