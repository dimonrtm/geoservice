---
title: "Охват полевого свидетельства"
type: value-object
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/field_observation, Wiki/commands/split_preserved_pipe_edge, Wiki/commands/record_service_restoration]
---

# Охват полевого свидетельства

## Meaning

Охват отвечает на вопрос, к какой части физического объекта, линии или набора точек относится именно это свидетельство. Для осмотра трубы это может быть локализованный дефект, обследованный отрезок с границами или только указание на трубу при неизвестной локализации. Для восстановления услуги это проверенный участок либо установленные точки услуги.

## Equality

При данном объекте и способе привязки два значения совпадают, если охватывают те же точки или те же установленные границы. Порядок перечисления точек роли не играет. Указание на трубу без локализации отличается от осмотра всей её длины. Дата и источник характеризуют само свидетельство. Два осмотра могут иметь одинаковый охват и разную дату.

## Immutability

После деления ребра исходный охват сохраняется. Новая привязка должна опираться на сведения о местоположении дефекта. Аналогично границу подтверждённого восстановления, съёмки или допуска нельзя распространить на соседнюю часть лишь из-за общего наряда или проекта.

Решения условной организации через `expert_repson`. [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
