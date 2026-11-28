---
title: RAW_inputs
type: index
status: active
created: 2026-05-30
updated: 2026-11-27
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

## Основание действующей доменной модели

27.11.2026 повторно обработан [UtilityGisEditor.md](documents/UtilityGisEditor.md) как единственный источник начальной доменной модели. Последующие уточнения обозначены в журнале как обработанные в действующей модели. Записи «Обработан ранее» относятся к прежнему срезу. [Каталог сценариев](../DDD_Wiki/use_cases/_info.md) · [Состояние модели](../DDD_Wiki/model_health.md).

## Журнал Поступлений

| Дата | Файл | Источник | Обработан |
|---|---|---|---|
| 2026-11-27 | [Ответы о полевых сведениях](documents/2026-11-27-field-information-answers.md) | 12 развилок и внешние свидетельства. [Принятое правило](../Wiki/policies/field_information.md), [инварианты](../DDD_Wiki/invariants/field_evidence_scope.md) и [переходы состояний](../DDD_Wiki/state_machines/_info.md). | Обработан совместно с анализом. [Покрытие обеих wiki](../DDD_Wiki/model_health.md#полнота-разбора-полевых-сведений). |
| 2026-11-27 | [Анализ изменений модели](documents/2026-11-27-field-information-model-analysis.md) | Отбор 16 вопросов и прирост по 12 исследованным. [Решения о пяти агрегатах](../DDD_Wiki/aggregates/_info.md) и [операции по каждому эпизоду](../DDD_Wiki/model_health.md#от-полевого-эпизода-к-операции). | Обработан совместно с ответами. [Для четырёх задач приняты варианты](../DDD_Wiki/use_cases/candidates/_info.md#исследование-полевых-сведений-от-27112026). NET-11 решён частично. |
| 2026-10-11 | `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md` | Интернет-исследование на основе `UtilityGisEditorRole.md`: 15 синтезированных ответов заказчика, 9 первичных источников; предложения требуют принятия, не являются реальным интервью | Обработан ранее |
| 2026-05-30 | `RAW_inputs/documents/спринт 1.odt` | Release 1 planning/requirements document; актуальность и трактовка подтверждены 2026-05-31 | Обработан ранее · [[../Code_wiki/архитектура/api_contract_first_release_requirements]] |
| 2026-06-01 | `RAW_inputs/documents/Ф2.md` | Research-обзор веб-ГИС collaborative editing для подготовки Ф2-Ф3 | Обработан ранее |
| 2026-06-03 | `RAW_inputs/documents/03.06.2026deep-research-report.md` | Deep research comparison для Ф3: альтернативы GeoService в сценарии `Utility GIS editor` | Обработан ранее |
| 2026-06-04 | `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` | Acceptance criteria для Ф4 walking skeleton `Utility GIS editor` | Обработан ранее |
| 2026-06-05 | `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md` | Детализация Ф4: end-to-end walking skeleton и минимальный `synthetic_utility_feeder_01` dataset | Обработан ранее |
| 2026-06-06 | `RAW_inputs/documents/utility_gis_editor_target_times.md` | Draft P95 acceptance targets для map/edit/validation/reconcile/conflict/post на малом utility demo dataset | Обработан ранее |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md` | Словарь домена `Utility GIS editing`: роли, network objects, versions, validation, conflicts, audit и canonical workflow | Обработан ранее · [[../Code_wiki/глоссарий/technical_terms]] |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_metrics.md` | North Star и secondary metrics для safe authoritative editing | Обработан ранее |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_post_problems.md` | Определение post-проблемы и 7-дневного correction window | Обработан ранее |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_manual_baseline_algorithm.md` | Алгоритм измерения ручного baseline на 10-20 work orders | Обработан ранее |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_risky_assumptions.md` | Три рискованных допущения и порядок их проверки | Обработан ранее |
| 2026-06-07 | `RAW_inputs/documents/utility_gis_editor_minimal_experiments.md` | Минимальные workflow, validation и conflict experiments | Обработан ранее |
| 2026-06-12 | `RAW_inputs/meetings/utility_gis_editor_answers.md` | Синтетическая репетиция интервью от первого лица; принята владельцем проекта как подтверждение design-сценария, но не как external user evidence | Обработан ранее |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_reviewer_answers.md` | Синтетическая репетиция ответов от имени `Reviewer`; поддерживает design-персону и reviewer JTBD, но не является external user evidence | Обработан ранее |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_editor_broad_domain_answers.md` | Расширенная синтетическая доменная репетиция `Utility GIS editor`: physical/logical network state, as-built/redlining и review package | Обработан ранее |
| 2026-06-13 | `RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md` | Расширенная синтетическая доменная репетиция `Reviewer`: review package, risk-based routing и publisher responsibility | Обработан ранее |
| 2026-06-14 | `RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md` | Доверенный design/research source `Utility GIS editor`: risk tiers, evidence, post blockers, audit и routing для следующего релиза; выше assistant-led chat workshop по иерархии доверия, но не является direct user interview | Обработан ранее |
| 2026-06-14 | `RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md` | Доверенный design/research source с синтезированными ответами `Editor` и `Reviewer` для Release 2 Conflict Explanation; не является direct user interview | Обработан ранее |
| 2026-06-14 | `RAW_inputs/documents/UtilityGisEditor.md` | Рыночная реконструкция редактора сети, четыре рабочих процесса, роли, данные и обмен. | Повторный ingest 27.11.2026 — [[DDD_Wiki/use_cases/candidates/_info]], [[Wiki/concepts/network_data]], [[DDD_Wiki/model_health]]. |
| 2026-06-20, редакции 2026-11-22 и 2026-11-24 | `RAW_inputs/documents/UtilityGisEditorRole.md` | Research source о реальной работе ролей, близких к `Utility GIS editor`: authoritative network change owner/editor, ArcGIS и QGIS/PostGIS/QField/GISwater stacks, version conflicts, dirty areas, field sync, role training и KPI; не является direct user interview. 22.11 — 98 документов о полевой работе, версиях и поставке. 24.11 — 97 рассказов практиков о проверке и передаче смене, 83 новых относительно прежнего корпуса | Обработан ранее |
| 2026-06-16 | `RAW_inputs/meetings/Reviwer Decision.md` | Design/architecture input для Release 2 Reviewer decision: package approval for post readiness, разделение approval/post authorization, post blockers, stale approval, repeat review и граница `High/Critical` для trace change; не является direct user interview | Обработан ранее |
| 2026-06-17 | `RAW_inputs/meetings/geometry_association_conflict_f1.md` | Research/design input для Release 2 why-now вокруг `geometry/association conflict`: feature diff vs network consequence, уточнение `Normal`/`High`/`Critical`, risk переусложнения и validation caveats; не является direct user interview | Обработан ранее |
| 2026-06-18 | `RAW_inputs/meetings/geometry_association_conflict_f2.md` | Research/design input для Ф2 Release 2 `geometry/association conflict`: primary user `Editor`, момент боли на edit/validate/reconcile/pre-post, текущий workaround и критерии safe post; не является direct user interview | Обработан ранее |
| 2026-06-19 | `RAW_inputs/meetings/geometry_association_conflict_f3.md` | Research/design input для Ф3 Release 2 `geometry/association conflict`: конкурентный baseline `ArcGIS native + SOP + экспертный handoff`, зоны good-enough baseline, критерии выбора, blockers и demo proof для unified evidence context; не является direct user interview или vendor due diligence | Обработан ранее |
| 2026-06-20 | `RAW_inputs/meetings/geometry_association_conflict_f4.md` | Research/design input для Ф4 Release 2 `geometry/association conflict`: canonical transformer terminal association scenario, read-only consequence package, MVP boundary, walking skeleton, audit object и stale/failure case; не является direct user interview или vendor due diligence | Обработан ранее |
| 2026-06-22 | `RAW_inputs/meetings/geometry_association_conflict_f5.md` | Research/design input для Ф5 Release 2 `geometry/association conflict`: value signal, workflow placement after reconcile, rollout roles, required integrations, non-goals, false-confidence risk, support package, acceptable claims и first rollout scenario; не является direct user interview или vendor due diligence | Обработан ранее |
| 2026-06-23 | `RAW_inputs/meetings/geometry_association_conflict_f6.md` | Research/design input для Ф6 Release 2 `geometry/association conflict`: обязательный состав conflict package, computed vs fixture evidence, state machine, stale rules, hard post blockers, audit object, API/events, P95 targets, observability, access constraints и future ADR candidates; не является direct user interview или production SLA | Обработан ранее |
| 2026-06-23 | `RAW_inputs/meetings/geometry_association_conflict_f7.md` | Research/design input для Ф7 Release 2 `geometry/association conflict`: `contract readiness pass rate`, zero false-safe guardrail, secondary metrics, stale/pre-post sidecar experiment, run data, manual baseline и course-change criteria; не является direct user interview или production SLA | Обработан ранее |
| 2026-06-23 | `RAW_inputs/meetings/geometry_association_conflict_f8.md` | Research/design closeout Ф8 для Release 2 `geometry/association conflict`: pre-post decision-support scope, ready-to-implement contract decisions, remaining human-validation hypotheses, acceptance gates, implementation contract v0.1, real validation checklist и non-goals; не является direct user interview или production SLA | Обработан ранее |
| 2026-06-24 | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` | Design/architecture input для review/post implementation contract: `Reviewer` как semantic approval, `Publisher` / demo-system action как technical post, `ReviewPackage`, state machine, evidence, risk tiers, stale policy, audit boundary и ближайший vertical slice; не является direct user interview | Обработан ранее |
| 2026-06-26 | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` | Design/architecture input для отдельного integrated review/post contract: полный путь `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`, system `post-gate`, computed `can_post`, safety-complete blockers, audit boundary и small-sprint framing; не является direct user interview | Обработан ранее |
| 2026-06-27 | `RAW_inputs/meetings/increment_after_open_workspace.md` | Design/architecture answers для code-aware `/discover`: ближайший инкремент после открытия workspace должен быть persisted edit slice (`update existing feature -> operation=updated -> readback diff -> draft validation flags`), а review/post слои откладываются до появления change set; не является direct user interview | Обработан ранее |
| 2026-06-28 | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md` | Design/architecture input для first persisted edit slice: persisted change как diff относительно baseline, first command `UpdateEditVersionFeatureGeometry`, event `EditVersionChangeSetPersisted`, `DraftVersionToken`, readback diff и basic draft validation; не является direct user interview | Обработан ранее |
| 2026-06-29 | `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` | Design/architecture input для уточнения first persisted edit slice: saved geometry diff как текущая проекция относительно baseline, readback persisted object + explicit baseline diff, event только для ненулевого diff, `DraftVersionToken` как draft concurrency token и stop-line до review/post; не является direct user interview | Обработан ранее |
| 2026-06-30 | `RAW_inputs/meetings/first_save_edit_version.md` | Design/architecture input для recommended first save model: geometry-only internal-vertex edit существующей line feature, full resulting snapshot как source of truth, computed diff, state-based readback proof, aggregate-level `DraftVersionToken`, AOI containment и stop-line до review/post; не является direct user interview | Обработан ранее |
| 2026-07-25 | `RAW_inputs/meetings/first_save_for_edit_version.md` | Принятые design/architecture answers для first save: full resulting geometry, одна line feature / одна внутренняя вершина, immutable baseline, AOI `CoveredBy`, atomic validation, aggregate token, обязательный `CommandId`, save/revert events и persisted readback; не является direct user interview или independently verified vendor research | Обработан ранее |
| 2026-07-26 | `RAW_inputs/meetings/tolerance_rules.md` | Экспертный design/research answer о позиционной точности, coordinate grid, идемпотентных повторах, базовом состоянии работы и before/after evidence; не является direct user interview или независимой проверкой внешних источников | Обработан ранее |
| 2026-07-31 | `RAW_inputs/meetings/demo_utility_gis.md` | Экспертный design/research answer о positional acceptance, spatial-reference metadata, eligible demo vertex и lifecycle-safe save retry; не является утверждённой data-product specification, direct user interview или независимой проверкой внешних ссылок | Обработан ранее |
| 2026-10-13 | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-expert-recovery-governance.md` | Синтез в манере expert_repson: анализ Utility GIS editor и 15 discovery-ответов; десять основных первичных веб-источников, не интервью | Обработан ранее |
| 2026-10-13 | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` | Новая редакция 15 ответов expert_repson; принятые решения условной организации, пять первичных источников, не интервью | Обработан ранее |
| 2026-10-16 | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research.md` | Исследование UtilityGisEditorRole по семи первичным веб-источникам и 15 ответов синтетической персоны; принятые уточнения условной организации | Обработан ранее |
| 2026-10-16 | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research.md` | 17 прочитанных первичных/методических веб-источников и 15 ответов о пригодности данных и качестве; синтетическая персона | Обработан ранее |
| 2026-10-16 | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-network-semantics-research.md` | 17 первичных веб-документов; 15 ответов о смысле правки и сетевых последствиях; решения условной организации | Обработан ранее |
| 2026-10-18 | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis.md` | Расширенное исследование 81 документа; 12 доменных выводов, provenance и границы применимости | Обработан ранее |
| 2026-10-18 | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-use-case-answers.md` | Ответы условной организации на 15 вопросов, аналитическая сценарная матрица | Обработан ранее |
| 2026-10-19 | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-research.md` | 77 прочитанных веб-документов, 35 новых URL относительно реестра 2026-10-18; десять уточнений: revision, зависимость evidence, время, отзыв, история и передача | Обработан ранее |
| 2026-10-19 | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-answers.md` | 15 ответов условной организации по тому же корпусу 77 документов, ручная карточка и аналитическая матрица | Обработан ранее |

| 2026-10-22 | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-research.md` | Исследование 84 внешних документов; выпуск, scope, применимость и исправление заключения; внешние факты и модель разделены | Обработан ранее |
| 2026-10-22 | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers.md` | 15 ответов на общем корпусе 84 документов, ручная карточка, аналитическая матрица; не интервью/runtime validation | Обработан ранее |

| 2026-11-07 | `RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-research.md` | Анализ UseCase и новых знаний: 80 внешних документов, 51 новый точный URL относительно прежних RAW; не 80 независимых свидетельств | Обработан ранее |
| 2026-11-07 | `RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-answers.md` | 15 ответов условной организации на общем корпусе 80 документов; ручная карточка и аналитическая матрица, не runtime validation | Обработан ранее |

| 2026-11-08 | `RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-research.md` | Анализ UseCase: 78 внешних документов, 42 ранее не встречавшихся точных URL; метод, охват, состояния знания и перенос представления | Обработан ранее |
| 2026-11-08 | `RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers.md` | 15 ответов на общем корпусе 78 документов; ручная карточка и аналитическая матрица, не runtime validation | Обработан ранее |

| 2026-11-08 | `RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-research.md` | Анализ 80 документов; 26 новых нормализованных URL; назначение геометрии, роли ключей и знаменатель полноты | Обработан ранее |
| 2026-11-08 | `RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-answers.md` | 15 ответов на общем корпусе 80 документов; решения условной организации, ручной протокол, не runtime validation | Обработан ранее |

| 2026-11-09 | RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-research.md | Анализ UseCase: 88 документов, 66 новых нормализованных URL; отзыв и коррекция публикации | Обработан ранее |
| 2026-11-09 | RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md | Два ответа discovery на общем корпусе 88 документов; решения условной организации и 15 аналитических сценариев | Обработан ранее |

| 2026-11-10 | RAW_inputs/research_results/2026-11-10-utility-gis-editor-dependencies-research.md | Анализ UseCase и новых знаний: 75 документов, 25 новых нормализованных URL | Обработан ранее |
| 2026-11-10 | RAW_inputs/research_results/2026-11-10-utility-gis-editor-dependencies-answers.md | Три ответа discovery на общем корпусе 75 документов, ручной протокол и 15 аналитических сценариев | Обработан ранее |
| 2026-11-21 | `RAW_inputs/research_results/2026-11-21-utility-gis-editor-asset-lifecycle-research.md` | Анализ UseCase по 102 внешним документам, сравнение подходов и прирост знаний | Обработан ранее |
| 2026-11-21 | `RAW_inputs/research_results/2026-11-21-utility-gis-editor-asset-lifecycle-answers.md` | Три решения условной организации и аналитические сценарии | Обработан ранее |
| 2026-11-22 | `RAW_inputs/research_results/2026-11-22-utility-gis-editor-governance-research.md` | Исследование UseCase по 101 внешнему документу, сравнение решений и прирост к прежней модели | Обработан ранее |
| 2026-11-22 | `RAW_inputs/research_results/2026-11-22-utility-gis-editor-governance-answers.md` | Ответы условной организации на DISC-2026-11-21-04…18, исключения и аналитические примеры | Обработан ранее |
| 2026-11-24 | `RAW_inputs/docs/241126.txt` | Русская подборка Melbourne Water и двух публикаций Esri о съёмке, трассировке и рабочей версии | Обработан ранее |
| 2026-11-24 | `RAW_inputs/docs/AWWA-2017-Leading-Business-Practices-in-Asset-Management.url` | Отчёт о практике операторов. [Отчёт AWWA](https://cms.jerseywaterworks.org/wp-content/uploads/2017/06/AWWA-2017-Leading-Business-Practices-in-Asset-Management.pdf). Для редактора использован кейс Downers Grove об охвате обследований | Обработан ранее |
| 2026-11-24 | `RAW_inputs/docs/Western-Virginia-Regional-Design-and-Construction-Standards-2024-Addendum-1.url` | Раздел CS-4 об измерении длины, контроле разметки и повторной телеинспекции. [Стандарт Western Virginia с Addendum 1](https://www.westernvawater.org/home/showpublisheddocument/14522/639010601448130000). | Обработан ранее |
| 2026-11-24 | `RAW_inputs/documents/2026-11-24-field-records-analysis.md` | 101 первичное свидетельство о полевых данных и прирост модели по 15 развилкам | Обработан ранее |
| 2026-11-24 | `RAW_inputs/documents/2026-11-24-field-records-answers.md` | Вопросы исходного сценария и решения условной организации по DISC-2026-11-24-01…15 | Обработан ранее |
| 2026-11-26 | `RAW_inputs/documents/2026-11-26-field-evidence-analysis.md` | Корпус из 99 первичных свидетельств и дополнительный материал, сравнение действий и решения по целям | Обработан ранее |
| 2026-11-26 | `RAW_inputs/documents/2026-11-26-field-evidence-answers.md` | Ответы по исходному сценарию и DISC-2026-11-26-01…02 | Обработан ранее |
| 2026-11-26 | `RAW_inputs/documents/2026-11-26-editor-practice-analysis.md` | 85 свидетельств практиков, 46 новых для корпуса. Сравнение подходов, проверок и рабочих целей | Обработан ранее |
| 2026-11-26 | `RAW_inputs/documents/2026-11-26-editor-practice-answers.md` | Ответы по роли редактора и DISC-2026-11-26-03, пять учебных случаев | Обработан ранее |
