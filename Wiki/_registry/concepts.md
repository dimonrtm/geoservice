---
title: Concepts Registry
type: index
status: active
created: 2026-06-24
updated: 2026-11-09
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, concept]
confidence: n/a
related: [Wiki/index]
---

# Concepts Registry

| Concept | Meaning | Related | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/concepts/authoritative_utility_workflow]] | Процесс от `WorkOrder` до authoritative post; ближайший кодовый слой сначала доказывает persisted edit change set. | [[DDD_Wiki/use_cases/utility_editor_workflow]] | high | `Vision_wiki/decisions/release_1_utility_workflow.md`; `RAW_inputs/meetings/increment_after_open_workspace.md` |
| [[Wiki/concepts/field_observation_acceptance]] | Принятие утверждений свидетельства с областью и контекстом организации | [[Wiki/policies/edit_change_justification_policy]] | high | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis.md` |
| [[Wiki/concepts/network_representation_and_operational_state]] | Геометрия, актив, отношения, эксплуатация и сценарий различаются | [[Wiki/policies/network_edit_semantics_policy]] | high | `RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis.md` |
| [[Wiki/concepts/change_basis_lifecycle]] | Редакция основания, время наблюдения и история решения отдельно от geometry | [[Wiki/policies/change_basis_revision_policy]] | high | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-research.md` |
| [[Wiki/concepts/evidence_dependency]] | Копии общего наблюдения не являются независимыми подтверждениями | [[Wiki/concepts/field_observation_acceptance]] | high | `RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-research.md` |

| [[Wiki/concepts/assessment_statement_lifecycle]] | Состояние, утверждение, выпуск и применимость различаются | [[Wiki/policies/assessment_issue_and_correction_policy]] | high | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-research.md` |
| [[Wiki/concepts/assessment_delivery_and_acceptance]] | Доставка, ограничения, обязанность и приёмка для цели различаются | [[Wiki/policies/assessment_issue_and_correction_policy]] | high | `RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-research.md` |

| [[Wiki/concepts/dataset_instance_and_record_identity]] | Логический набор, экземпляр, запись и обозначаемый актив различаются | [[Wiki/specifications/demo_dataset_instance_qualified]] | high | `RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-research.md` |
| [[Wiki/concepts/coordinate_operation_provenance]] | CRS, операция, ресурсы и история координат отдельно от сетки и точности | [[Wiki/policies/demo_dataset_qualification_policy]] | high | `RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-research.md` |

## Уточнение существующих понятий — 2026-11-08

По [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-research]]: [[Wiki/concepts/field_observation_acceptance]] — метод и охват свойства; [[Wiki/concepts/assessment_statement_lifecycle]] — пределы отрицательного результата проверки; [[Wiki/concepts/dataset_instance_and_record_identity]] — сверка конечного представления после переноса; [[Wiki/concepts/assessment_delivery_and_acceptance]] — отправка, применение и наблюдение результата. Новых дублирующих понятий нет.

## Представление, идентификатор и полнота — 2026-11-08

По [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-representation-research]] дополнены существующие понятия: [[Wiki/concepts/network_representation_and_operational_state]] — назначение геометрии; [[Wiki/concepts/dataset_instance_and_record_identity]] — физический ключ, идентификатор обмена и актив; [[Wiki/concepts/assessment_statement_lifecycle]] — знаменатель полноты. Новых дублирующих нод нет.

## Коррекция публикации — 2026-11-09

| Concept | Meaning | Confidence | Source |
| --- | --- | --- | --- |
| [[Wiki/concepts/published_result_correction_case]] | Область ответственности за дефект опубликованных данных/evidence, связанные циклы и остатки | high | RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md |
