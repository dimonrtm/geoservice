---
title: RAW_inputs
type: index
status: active
created: 2026-05-30
updated: 2026-06-14
source: null
tags: [raw-inputs, source-of-truth]
---

# RAW_inputs

Здесь хранятся сырые материалы проекта. Новые материалы добавляются, но исходные файлы не переписываются на месте.

## Папки

- [[meetings/_info]] - транскрипты и исходные заметки встреч.
- [[documents/_info]] - требования, спецификации, презентации и PDF.
- [[code/_info]] - фрагменты кода, ссылки на коммиты и технические выдержки для разбора.
- [[docs/_info]] - внешняя или импортированная документация.
- [[chats/_info]] - экспорты переписок, писем и мессенджеров.
- [[research_results/_info]] - результаты research.

## Журнал Поступлений

| Дата | Файл | Источник | Обработан |
|---|---|---|---|
| 2026-05-30 | `RAW_inputs/documents/спринт 1.odt` | Release 1 planning/requirements document; актуальность и трактовка подтверждены 2026-05-31 | Да: [[../Vision_wiki/chats/2026-05-30-release-1-document]], [[../Vision_wiki/concepts/first_release_mvp]], [[../Vision_wiki/solution/USM]], [[../Code_wiki/архитектура/api_contract_first_release_requirements]] |
| 2026-06-01 | `RAW_inputs/documents/Ф2.md` | Research-обзор веб-ГИС collaborative editing для подготовки Ф2-Ф3 | Да: [[../Vision_wiki/chats/2026-06-01-phase-f2-collaborative-editing-research]], [[../Vision_wiki/concepts/collaborative_editing_models]], [[../Vision_wiki/entities/personas/collaborative_editing_archetypes]], [[../Vision_wiki/entities/competitors/collaborative_editing_alternatives]] |
| 2026-06-03 | `RAW_inputs/documents/03.06.2026deep-research-report.md` | Deep research comparison для Ф3: альтернативы GeoService в сценарии `Utility GIS editor` | Да: [[../Vision_wiki/chats/2026-06-03-phase-f3-alternatives]], [[../Vision_wiki/entities/competitors/collaborative_editing_alternatives]], [[../Vision_wiki/concepts/lean_canvas]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-04 | `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` | Acceptance criteria для Ф4 walking skeleton `Utility GIS editor` | Да: [[../Vision_wiki/chats/2026-06-04-phase-f4-solution-scope]], [[../Vision_wiki/solution/USM]], [[../Vision_wiki/solution/roadmap]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-05 | `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md` | Детализация Ф4: end-to-end walking skeleton и минимальный `synthetic_utility_feeder_01` dataset | Да: [[../Vision_wiki/chats/2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]], [[../Vision_wiki/solution/USM]], [[../Vision_wiki/solution/architecture_vision]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-06 | `RAW_inputs/documents/utility_gis_editor_target_times.md` | Draft P95 acceptance targets для map/edit/validation/reconcile/conflict/post на малом utility demo dataset | Да: [[../Vision_wiki/chats/2026-06-06-utility-gis-editor-target-times]], [[../Vision_wiki/solution/nfr]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md` | Словарь домена `Utility GIS editing`: роли, network objects, versions, validation, conflicts, audit и canonical workflow | Да: [[../Vision_wiki/chats/2026-06-07-utility-gis-editor-domain-dictionary]], [[../Vision_wiki/concepts/utility_gis_editing_domain]], [[../Code_wiki/глоссарий/technical_terms]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_metrics.md` | North Star и secondary metrics для safe authoritative editing | Да: [[../Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks]], [[../Vision_wiki/concepts/metrics]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_post_problems.md` | Определение post-проблемы и 7-дневного correction window | Да: [[../Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks]], [[../Vision_wiki/concepts/metrics]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_manual_baseline_algorithm.md` | Алгоритм измерения ручного baseline на 10-20 work orders | Да: [[../Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks]], [[../Vision_wiki/concepts/metrics]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_risky_assumptions.md` | Три рискованных допущения и порядок их проверки | Да: [[../Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_minimal_experiments.md` | Минимальные workflow, validation и conflict experiments | Да: [[../Vision_wiki/chats/2026-06-07-phase-f7-metrics-and-risks]], [[../Vision_wiki/decisions/risk_assumption_log]], [[../Vision_wiki/decisions/followups/index]] |
| 2026-06-12 | `RAW_inputs/meetings/utility_gis_editor_answers.md` | Синтетическая репетиция интервью от первого лица; принята владельцем проекта как подтверждение design-сценария, но не как external user evidence | Да: [[../Vision_wiki/chats/2026-06-12-utility-gis-editor-synthetic-interview-rehearsal]], [[../Vision_wiki/entities/personas/utility_gis_editor]], [[../Vision_wiki/concepts/jtbd]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_reviewer_answers.md` | Синтетическая репетиция ответов от имени `Reviewer`; поддерживает design-персону и reviewer JTBD, но не является external user evidence | Да: [[../Vision_wiki/chats/2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]], [[../Vision_wiki/entities/personas/utility_gis_reviewer]], [[../Vision_wiki/concepts/jtbd]], [[../Vision_wiki/decisions/risk_assumption_log]], [[../Vision_wiki/decisions/followups/index]] |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_editor_broad_domain_answers.md` | Расширенная синтетическая доменная репетиция `Utility GIS editor`: physical/logical network state, as-built/redlining и review package | Да: [[../Vision_wiki/chats/2026-06-13-utility-gis-editor-broad-domain-rehearsal]], [[../Vision_wiki/concepts/utility_gis_editing_domain]], [[../Vision_wiki/entities/personas/utility_gis_editor]], [[../Vision_wiki/concepts/jtbd]], [[../Vision_wiki/decisions/risk_assumption_log]] |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md` | Расширенная синтетическая доменная репетиция `Reviewer`: review package, risk-based routing и publisher responsibility | Да: [[../Vision_wiki/chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]], [[../Vision_wiki/concepts/utility_gis_editing_domain]], [[../Vision_wiki/entities/personas/utility_gis_reviewer]], [[../Vision_wiki/concepts/jtbd]], [[../Vision_wiki/decisions/followups/index]] |
| 2026-06-14 | `RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md` | Доверенный design/research source `Utility GIS editor`: risk tiers, evidence, post blockers, audit и routing для следующего релиза; выше assistant-led chat workshop по иерархии доверия, но не является direct user interview | Да: [[../Vision_wiki/chats/2026-06-14-utility-gis-editor-conflict-routing-synthetic-research]], [[../Vision_wiki/decisions/conflict_resolution_routing]], [[../Vision_wiki/decisions/conflicts/2026-06-14-next-release-conflict-routing-responsibility]], [[../Vision_wiki/decisions/risk_assumption_log]], [[../Vision_wiki/decisions/followups/index]] |
| 2026-06-14 | `RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md` | Доверенный design/research source с синтезированными ответами `Editor` и `Reviewer` для Release 2 Conflict Explanation; не является direct user interview | Да: [[../Vision_wiki/chats/2026-06-14-release-2-conflict-explanation-editor-reviewer-research]], [[../Vision_wiki/decisions/release_2_conflict_explanation]], [[../Vision_wiki/decisions/conflicts/2026-06-14-trace-risk-tier-boundary]], [[../Vision_wiki/decisions/risk_assumption_log]], [[../Vision_wiki/decisions/followups/index]] |
