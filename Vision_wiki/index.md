---
title: Vision_wiki
type: index
status: active
created: 2026-05-30
updated: 2026-06-27
source: null
tags: [vision-wiki, product]
---

# Vision_wiki

Продуктовые знания и решения GeoService.

## Структура

- [[_templates/_info]] - шаблоны продуктовых и decision-нод.
- [[chats/_info]] - чек-листы встреч и структурированные сводки разговоров.
- [[concepts/_info]] - продуктовые и доменные концепты.
- [[decisions/_info]] - решения, assumptions, конфликты и follow-up'ы.
- [[entities/_info]] - стейкхолдеры, персоны, конкуренты и связанные сущности.
- [[solution/_info]] - solution view, user story map, roadmap и NFR notes.

## Стартовые Ноды

- [[../index]] - корневой индекс знаний проекта.
- [[../memory/project-state]] - живое состояние проекта.
- [[../Code_wiki/index]] - техническая wiki.

## Solution Drafts

- [[concepts/about_project]] - стартовый discovery-контекст GeoService.
- [[concepts/product_vision_board]] - draft vision после Ф1.
- [[concepts/lean_canvas]] - draft Lean Canvas после Ф1.
- [[decisions/risk_assumption_log]] - гипотезы и риски discovery.
- [[entities/stakeholders/dmitry_popov]] - владелец решений pet-проекта.
- [[concepts/first_release_mvp]] - Release 1 MVP и границы совместного редактирования.
- [[solution/USM]] - User Story Map Release 1.
- [[solution/roadmap]] - roadmap Release 1 по дням и later scope.
- [[solution/nfr]] - Release 1 NFR: performance, security, data, maintainability.
- [[solution/architecture_vision]] - high-level architecture vision Release 1.
- [[chats/2026-05-30-release-1-document]] - summary source-документа `спринт 1.odt`.
- [[chats/2026-05-31-initial-discover]] - ответы первого `/discover`.
- [[chats/2026-05-31-phase-f1-why-now]] - результаты Ф1: исследовательская мотивация и why-now.
- [[chats/2026-06-01-phase-f2-collaborative-editing-research]] - research для Ф2-Ф3 по сценариям и альтернативам collaborative editing.
- [[concepts/collaborative_editing_models]] - четыре модели collaborative editing геометрии и гипотезы для GeoService.
- [[entities/personas/collaborative_editing_archetypes]] - семь модельных архетипов пользователей и история выбора primary scenario.
- [[entities/competitors/collaborative_editing_alternatives]] - Ф3-карта альтернатив для `Utility GIS editor`: ArcGIS Enterprise baseline, non-Esri URL follow-up и niche GeoService.
- [[chats/2026-06-02-phase-f2-users-and-pain]] - ответы Ф2: primary research-persona `Utility GIS editor`, utility workflow и synthetic validation.
- [[entities/personas/authoritative_gis_editing_candidates]] - история выбора между `Utility GIS editor` и кадастровым инженером.
- [[entities/personas/utility_gis_editor]] - primary research-persona GeoService для utility authoritative editing.
- [[concepts/jtbd]] - primary JTBD `Utility GIS editor` и deferred кадастровый JTBD.
- [[chats/2026-06-03-phase-f3-alternatives]] - deep research summary Ф3: альтернативы, blockers, demo-сценарий и URL follow-up'ы.
- [[chats/2026-06-04-phase-f4-solution-scope]] - ответы Ф4: demo-scope, walking skeleton, synthetic utility dataset и non-goals.
- [[chats/2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]] - детализация Ф4 walking skeleton и минимального `synthetic_utility_feeder_01` dataset.
- [[chats/2026-06-05-phase-f5-business-rollout]] - ответы Ф5: local Docker Compose rollout, developer demo, learning value и rollout constraints.
- [[decisions/constraints]] - ограничения demo после Ф5: synthetic data, local runtime, integration boundaries и promise boundaries.
- [[chats/2026-06-06-phase-f6-constraints-and-nfr]] - ответы Ф6: reference hardware, Chrome, startup/reset, JWT roles, audit persistence, observability и `import GeoJSON`.
- [[chats/2026-06-06-utility-gis-editor-target-times]] - draft P95 acceptance targets для map, edit, validation, reconcile, conflict view и post.
- [[chats/2026-06-07-utility-gis-editor-domain-dictionary]] - summary словаря домена `Utility GIS editing` и его границы относительно demo-scope.
- [[concepts/utility_gis_editing_domain]] - канонический язык ролей, сетевых объектов, edit version, validation, reconcile, conflict и post.
- [[chats/2026-06-07-phase-f7-metrics-and-risks]] - ответы Ф7: North Star, safety gates, baseline, evidence и risk register.
- [[concepts/metrics]] - измерительный контракт `Safe Authoritative Post Rate`, secondary metrics и guardrails.
- [[chats/2026-06-11-phase-f8-release-1-closeout]] - Ф8: пересборка Release 1 вокруг полного `Utility GIS editor` workflow.
- [[decisions/release_1_utility_workflow]] - активное решение: generic GIS остается foundation, Release 1 заканчивается authoritative post и audit.
- [[decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]] - разрешение конфликта между старым generic scope и новым utility workflow.
- [[chats/2026-06-12-utility-gis-editor-user-interview-checklist]] - чек-лист 30-минутного интервью с реальным GIS-редактором о фактическом workflow и боли.
- [[chats/2026-06-12-utility-gis-editor-synthetic-interview-rehearsal]] - синтетическая репетиция принята как подтверждение design-сценария и зоны ценности единого evidence context.
- [[chats/2026-06-13-utility-gis-reviewer-user-interview-checklist]] - чек-лист 30-минутного интервью с реальным `Reviewer` инженерной GIS-сети о критериях решения, возвратах и публикации.
- [[chats/2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]] - синтетическая репетиция reviewer workflow, критериев безопасного решения и единого evidence context.
- [[entities/personas/utility_gis_reviewer]] - design-персона проверяющего инженерной GIS-сети; границы `post`, routing очереди и separation of duties требуют внешней проверки.
- [[chats/2026-06-13-utility-gis-editor-broad-domain-rehearsal]] - broad-domain synthetic framing editor workflow через physical/logical network state, as-built и review package.
- [[chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]] - broad-domain synthetic framing reviewer как контроля между field reality, GIS model и operational systems.
- [[chats/2026-06-14-geometry-association-conflict-resolution-workshop]] - superseded assistant-led design input; сохранен как история развилки.
- [[decisions/conflict_resolution_routing]] - planned решение следующего релиза по доверенному RAW source.
- [[chats/2026-06-14-utility-gis-editor-conflict-routing-synthetic-research]] - доверенный design/research source: risk tiers, evidence, post blockers, audit и routing.
- [[decisions/conflicts/2026-06-14-next-release-conflict-routing-responsibility]] - разрешенный provenance-конфликт; RAW source каноничен относительно chat workshop.
- [[chats/2026-06-14-release-2-conflict-explanation-editor-reviewer-research]] - доверенный синтез требований `Editor` и `Reviewer` к consequence-first explanation.
- [[decisions/release_2_conflict_explanation]] - planned contract Release 2 для explanation, evidence, stale approval, audit и post gates.
- [[decisions/conflicts/2026-06-14-trace-risk-tier-boundary]] - resolved policy по границе `High/Critical`: trace change становится `Critical` только при изменении authoritative network behavior.
- [[chats/2026-06-16-release-2-reviewer-decision]] - design/architecture input: reviewer decision как package approval for post readiness, разделение approval/post authorization, post blockers и resolved trace boundary.
- [[chats/2026-06-17-geometry-association-conflict-f1]] - research/design input: why-now для Release 2 `geometry/association conflict`, feature diff vs network consequence, refined `Normal`/`High`/`Critical` и validation caveats.
- [[chats/2026-06-18-geometry-association-conflict-f2]] - research/design input Ф2: primary user `Editor`, момент боли, текущий workaround и safe post criteria для `geometry/association conflict`.
- [[chats/2026-06-19-geometry-association-conflict-f3]] - research/design input Ф3: конкурентный baseline `ArcGIS native + SOP + экспертный handoff`, good-enough зоны, blockers и demo proof для unified evidence context.
- [[chats/2026-06-20-geometry-association-conflict-f4]] - research/design input Ф4: canonical transformer terminal association scenario, read-only consequence package, walking skeleton, audit object и stale/failure case для Release 2.
- [[chats/2026-06-22-geometry-association-conflict-f5]] - research/design input Ф5: internal developer demo rollout, value signal, workflow placement after reconcile, support package и следующий артефакт `implementation contract`.
- [[chats/2026-06-23-geometry-association-conflict-f6-checklist]] - planned checklist Ф6: ограничения и NFR для Release 2 `implementation contract` перед записью ответов в RAW.
- [[chats/2026-06-23-geometry-association-conflict-f6]] - research/design input Ф6: implementation contract boundary, evidence package, stale rules, hard blockers, audit, API/events, P95 и observability для Release 2 demo.
- [[chats/2026-06-23-geometry-association-conflict-f7-checklist]] - planned checklist Ф7: метрики, risks, experiments и guardrails для проверки Release 2 consequence package.
- [[chats/2026-06-23-geometry-association-conflict-f7]] - research/design input Ф7: `contract readiness pass rate`, zero false-safe guardrail, secondary metrics, stale/pre-post sidecar experiment, run data, manual baseline и course-change criteria для Release 2 demo.
- [[chats/2026-06-23-geometry-association-conflict-f8-checklist]] - planned checklist Ф8: closeout Release 2 `geometry/association conflict`, ready-to-implement decisions, remaining blockers, RAW artifacts, wiki updates и следующие шаги.
- [[chats/2026-06-23-geometry-association-conflict-f8]] - research/design closeout Ф8: pre-post decision-support scope, ready-to-implement contract decisions, remaining validation hypotheses, acceptance gates, non-goals и следующий implementation contract v0.1.
- [[chats/2026-06-24-implementation-contract-for-review-and-post]] - design/architecture input для review/post implementation contract: `Reviewer` как semantic approval, `Publisher` / demo-system action как technical post, `ReviewPackage`, stale policy, hard blockers, audit boundary и ближайший vertical slice.
- [[chats/2026-06-26-ic-review-package-and-simulated-post]] - design/architecture input для отдельного integrated review/post contract: `submit_for_review`, reviewer decision, computed `can_post`, simulated post, durable audit, system `post-gate`, safety-complete veto set и small-sprint framing.
- [[chats/2026-06-27-increment-after-open-workspace]] - code-aware discovery answers: ближайший инкремент после открытия workspace должен быть persisted edit slice, а review/post начинается только после change set.
- [[chats/2026-06-14-utility-gis-editor-market-research]] - доверенное market research по полному Use Case, vendors и product families.
- [[chats/2026-06-20-utility-gis-editor-role-research]] - research source о реальной работе роли: authoritative network change owner/editor, ArcGIS и QGIS/PostGIS/QField/GISwater stacks, field sync, topology QA, training и KPI.
- [[concepts/operational_utility_gis]] - справочная рыночная категория из network editor, field execution и integration hub.
- [[entities/competitors/utility_gis_editor_market_landscape]] - международные и русскоязычные utility GIS референсы.

## Открытые Вопросы

- [[decisions/followups/index]] - очередь открытых вопросов и post-ingest correction candidates.
