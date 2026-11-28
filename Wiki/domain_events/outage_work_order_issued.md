---
title: "Бригаде выдано оперативное задание"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_work_order, Wiki/commands/issue_outage_work_order, Wiki/value_objects/calculated_outage_extent]
---

# Бригаде выдано оперативное задание

## Source Aggregate

[[DDD_Wiki/aggregates/network_work_order|Наряд]] определяет адресованный бригаде объём работ.

## Happened In The Past

Диспетчер определил работы на сети и передал задание полю. В наряде виден расчётный охват, известный на момент выдачи. Например, при спорном положении задвижки в нём есть общие всем вариантам ветви, возможные дополнительные ветви и просьба проверить задвижку.

## Downstream Reactions

Бригада получает предмет проверки и возвращает сведения по этому заданию. Последующий ответ позволяет уточнить охват. Само задание не устанавливает фактический перерыв или восстановление услуги. Судьба ранее выданного задания после новой офисной публикации остаётся открытой в NET-15. [[Wiki/_registry/questions|Реестр вопросов]].

Решения условной организации через `expert_repson`. [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
