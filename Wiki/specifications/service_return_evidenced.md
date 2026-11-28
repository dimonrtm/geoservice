---
title: "Возврат услуги подтверждён в указанной части задания"
type: specification
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_work_order, Wiki/commands/record_service_restoration, Wiki/value_objects/evidence_extent]
---

# Возврат услуги подтверждён в указанной части задания

## Predicate

Установлены участок или точки в охвате наряда, момент проверки и наблюдаемый признак возврата услуги. Подходит полевая проверка услуги либо независимое подтверждение, относящееся к этой части. Проверку выполняют для каждого объёма, который диспетчер собирается закрыть.

## Failure Meaning

Отметка «ремонт окончен», расчёт трассировки, молчание прибора либо сведения только о соседней ветви оставляют восстановление в спорном объёме неподтверждённым. Уже подтверждённую часть можно учесть отдельно. Исследование оставляет выбор показателя и достаточных контрольных точек для конкретного водопровода открытым.

Решения условной организации через `expert_repson`. [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
