---
title: Specifications Registry
type: index
status: active
created: 2026-06-24
updated: 2026-11-09
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, specification]
confidence: n/a
related: [Wiki/index]
---

# Specifications Registry

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/editor_assigned_to_work_order]] | Текущий активный editor является назначенным исполнителем. | Нельзя открыть edit version/workspace. | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/specifications/edit_version_has_persisted_change_set]] | В `EditVersion` есть current diff одной line feature и одной внутренней вершины относительно базового состояния работы; response + durable readback доказывают persisted state. | Workspace пока read-only или UI-only draft; submit/review преждевременны. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md` |
| [[Wiki/specifications/edit_version_basic_draft_validation]] | First save канонизирует изменённую вершину, проверяет hard guards и отдельно фиксирует `POSITIONAL_ACCURACY_UNVERIFIED`, пока нет specification/evidence. | Hard failure отклоняет save атомарно; unverified positional status разрешает working draft, но не review. | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md`; `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/specifications/edit_version_ready_for_review]] | Persisted change set, basic draft validation, `POSITIONAL_ACCURACY_VERIFIED`, freshness/evidence, затем полный reconcile/default predicate. | Review преждевременен или blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/first_save_for_edit_version.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/specifications/post_allowed]] | Computed `can_post`: package approved, not stale, no absolute veto, `Default` fresh, required evidence complete, pre-post gate passed. | Simulated/technical post blocked. | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |

| [[Wiki/specifications/simulated_line_positional_acceptance]] | SIM-UGIS-POS-001 v1.0: полный scope, max(e+u)<=0,50 м, u<=0,10 м | Учебные pass/fail/unverified; не автоматический backend VERIFIED | high | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |

| [[Wiki/specifications/editing_resumption_allowed]] | Доказанный прежний исход, актуальное чтение, действующие права/контекст и осознанное актуальное намерение | Новая запись запрещена при невыполнении условий; recovery retry остаётся способом установить исход | high | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research.md` |
| [[Wiki/specifications/saved_line_quality_assessment]] | Связанное сохранённое состояние, пригодное evidence, полный охват и доказательство прежнего критерия | Не принято или непроверено с сохранением причин по участкам; не новый server status | high | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research.md` |
| [[Wiki/specifications/line_edit_exercise_completed]] | Объект, пригодные условия, намерение, receipt/current/baseline и заявленная ветка проверены | Учебная цель не доказана; причина устанавливается отдельно | high | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-use-case-answers.md` |
| [[Wiki/specifications/line_edit_basis_applicable]] | Установлены задача/состояние, редакция/охват, происхождение/время и последствия пересмотра | Недостаточно оснований для конкретного вывода; не автоматический Revert | high | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-answers.md` |

| [[Wiki/specifications/assessment_statement_usable]] | Состояние/цель/scope, прослеживаемый выпуск и действующая применимость | Нельзя опираться на утверждение для этой цели; не автоматический Revert | high | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers.md` |

| [[Wiki/specifications/demo_dataset_instance_qualified]] | Установлены экземпляр/контекст, policy, структура/AOI, ветка и прослеживаемые свидетельства | Допуск для заявленного упражнения не доказан; не новый Save guard | high | `RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-answers.md` |

## Уточнение доказательств — 2026-11-08

[[Wiki/specifications/demo_dataset_instance_qualified]] уточняет пункты 2–5 предиката: метод, фактический охват и состояние каждого наблюдения; частичный результат не означает проверку всего набора. Источник — [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers]]. Фактические metadata/fixture не подтверждены.

## Уточнение представления — 2026-11-08

[[Wiki/specifications/demo_dataset_instance_qualified]] связывает свидетельства с назначением геометрии, ролью идентификаторов и областью утверждения о полноте. Источник: [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-answers]]. Прежние инварианты и независимость технического/позиционного результата сохранены.

## Завершение коррекции — 2026-11-09

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/published_result_correction_closed]] | Доказанный результат/охват, связи, проверки, уведомление и явная судьба обязательных остатков | Разбор не завершён либо закрывает только ограниченную область с переданным остатком | high | RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md |

[[Wiki/specifications/post_allowed]] дополнен запретом post после принятого отзыва и запретом второй неразобранной попытки; чтение can_post не резервирует допуск. Источник — [[RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers]].

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/dependent_work_step_allowed]] | Все действующие обязательства этапа выполнены применимыми принятыми результатами, остатки приняты, обычные guards соблюдены | Удержание зависимого этапа с причиной | high | RAW_inputs/research_results/2026-11-10-utility-gis-editor-dependencies-answers.md |
