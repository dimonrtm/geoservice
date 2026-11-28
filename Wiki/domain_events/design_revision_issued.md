---
title: "Редакция проекта выдана для работ"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/use_cases/as_built_workflow, Wiki/commands/issue_design_for_construction, Wiki/value_objects/design_comparison_basis]
---

# Редакция проекта выдана для работ

## Source Aggregate

Проектный контур передал подрядчику трассу для выполнения работ. В редакторе сохраняют ссылку на выданную редакцию и её охват. Самостоятельный корень проектного согласования источником не установлен.

## Happened In The Past

Проектировщик передал подрядчику определённую редакцию согласованной трассы для указанной части и работ. При сверке редактор может указать, что действительно было выдано до их выполнения.

## Downstream Reactions

Когда появляется последующее утверждённое изменение, его сопоставляют с этой частью и работой. Выданная редакция остаётся частью истории основания. При молчании нового распоряжения об уже построенной части сохраняют факт съёмки и приостанавливают заключение о соответствии. [[Wiki/specifications/project_revision_applicable|Применимость редакции]].

Решения условной организации через `expert_repson`. [NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
