---
title: "Передать согласованную трассу для строительства"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/use_cases/as_built_workflow, Wiki/domain_events/design_revision_issued, Wiki/value_objects/design_comparison_basis]
---

# Передать согласованную трассу для строительства

## Actor

Проектировщик, передающий материалы подрядчику.

## Target

Редакция проектной трассы для определённой части и работ.

## Preconditions

Проектировщик подготовил трассу или изменение сети, сверил решение с ГИС-правилами и согласовал материалы для передачи.

## Outcome

Сохраняются связь выданной редакции с частью трассы и ссылки на последующие утверждённые изменения. Подрядчик получает основание, по которому выполняет указанную работу. Редактор затем сопоставляет с ним исполнительную съёмку. Если новый чертёж поступает после укладки части трассы, для ранее выполненной части потребуется установить применимость распоряжения. Выдача нового комплекта сама по себе не подтверждает исполнение или ввод.

Решения условной организации через `expert_repson`. [NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
