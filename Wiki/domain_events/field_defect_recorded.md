---
title: "Дефект зафиксирован при осмотре"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/field_observation, DDD_Wiki/aggregates/network_asset, Wiki/commands/record_operational_restriction]
---

# Дефект зафиксирован при осмотре

## Source Aggregate

[[DDD_Wiki/aggregates/field_observation|Полевое наблюдение]] содержит материал конкретного осмотра и его охват. Для опознанного объекта [[DDD_Wiki/aggregates/network_asset|физический актив]] учитывает дефект в истории с привязкой к этому материалу.

## Happened In The Past

В результате осмотра сохранены наблюдаемый дефект, место и дата. Для опознанной трубы наблюдение доступно в её истории с исходным охватом. При повторном осмотре сведения о дефекте могут дополниться новыми наблюдениями.

## Downstream Reactions

Эксплуатация получает результат для оценки работ. Для изменения доступности участка требуется отдельное подтверждение ограничения, отказа или вывода. Повторное обследование может дополнить историю до принятия такого решения.

Решения условной организации через `expert_repson`. [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
