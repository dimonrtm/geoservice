---
title: Policies Registry
type: index
status: active
created: 2026-06-24
updated: 2026-10-22
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, policy]
confidence: n/a
related: [Wiki/index]
---

# Policies Registry

| Policy                                                  | Rule                                                                                                                                                                             | Decision Outcome                                                         | Confidence | Source                                                                                          |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------- |
| [[Wiki/policies/editor_recovery_policy]]                | Принято 2026-10-12: удерживать намерение, выяснять неизвестный исход, не затирать свежую геометрию старым ответом                                                                | Сравнение, прежний retry либо новое явное намерение                      | high       | `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md`           |
| [[Wiki/policies/geometry_quality_escalation_policy]]    | Прежний запрет нулевых XY-сегментов; обязанности и dependency scope приняты                                                                                                      | Отдельный ремонт источника, доказательное разрешение; immutable baseline | high       | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |
| [[Wiki/policies/change_history_retention_policy]]       | SIM-UGIS-RET-001 v1.0: история/архив 10 лет, карточки 3 года, debug 30 дней; удержания                                                                                           | Demo без автоматической очистки; реализация отдельно                     | high       | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |
| [[Wiki/policies/edit_geometry_precision_policy]]        | Канонизировать server-side только изменённую вершину по metadata сохраняющего dataset, затем проверить hard guards; не выполнять скрытый snapping или full-line renormalization. | changed/no-op/rejected                                                   | high       | `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md`             |
| [[Wiki/policies/positional_accuracy_acceptance_policy]] | SIM-UGIS-POS-001 v1.0; полный evidence scope и событийная переоценка                                                                                                             | Учебный pass отдельно; first-save остаётся UNVERIFIED                    | high       | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |
| [[Wiki/policies/reviewer_post_policy]]                  | `Reviewer` принимает `approve package`, `return for changes`, `request evidence` или `escalate`; stale/block вычисляет система.                                                  | approved/returned/evidence_requested/escalated                           | high       | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`                                   |
| [[Wiki/policies/stale_approval_policy]]                 | Изменения `Default`, geometry, association, network attribute, terminal config, validation, trace/subnetwork или evidence делают approval устаревшим.                            | Repeat review или recompute package                                      | high       | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`                                   |
| [[Wiki/policies/recovery_case_resolution_policy]]       | Один цикл/5 минут; поддержка 15/60 минут активной сессии; явная передача и outcome отдельно от current                                                                           | Продолжить при доказательствах и guards либо оставить разбор открытым    | high       | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |
| [[Wiki/policies/edit_change_justification_policy]]      | Основание WorkOrder; пояснение исключения обязательно до review                                                                                                                  | Technical Save без нового обязательного параметра                        | high       | `RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md` |
| [[Wiki/policies/demo_dataset_qualification_policy]] | Паспорт, фактический набор и правила версии сверяются; техническая цель отделена от позиционной | Пригодность упражнения либо разбор расхождений без ремонта baseline | high | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-data-quality-research.md` |
| [[Wiki/policies/network_edit_semantics_policy]] | Различать смысл правки, зависимости и стадии результата; сохранять границы среза | Обоснованная правка, ограниченный частичный результат либо отдельный разбор | high | `RAW_inputs/research_results/2026-10-16-utility-gis-editor-network-semantics-research.md` |
| [[Wiki/policies/intentional_line_editing_policy]] | Явная идентичность, намерение, область отмены и доказательство записи | Осознанная попытка, результат или разбор | high | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-use-case-answers.md` |

## Уточнение действующих правил 2026-10-16

[[Wiki/policies/editor_recovery_policy]] и [[Wiki/policies/recovery_case_resolution_policy]] дополнены по [[RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research]]: независимость исхода/current, подтверждение продолжения, один наряд в одном окне учебной сессии и закрытие разбора без допуска к записи. Новая [[Wiki/specifications/editing_resumption_allowed]] сохраняет текущие guards.

## Пересмотр основания

| Policy | Rule | Outcome | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/policies/change_basis_revision_policy]] | Пересмотр задания, источника и объяснения по влиянию на утверждения | Эквивалентность, новое основание, ограничение либо разбор; без нового Save guard | high | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-answers.md` |

| [[Wiki/policies/assessment_issue_and_correction_policy]] | Выпуск, спор, исправление и уведомление по области/воздействию | Применимое ограниченное утверждение либо явный дальнейший разбор | high | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers.md` |
