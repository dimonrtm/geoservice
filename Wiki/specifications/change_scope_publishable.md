---
title: "Выделенный объём готов к публикации"
type: specification
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/commands/publish_network_changes, Wiki/policies/publication]
---

# Выделенный объём готов к публикации

## Predicate

Известно, какой объём изменений редактор предъявил к публикации. Его правила и топология проверены, выявленные в нём ошибки исправлены, конфликты разрешены и на этот состав получено утверждение. При таком наборе оснований уполномоченный участник может включить изменения в официальный слой.

## Failure Meaning

Если утверждена только измеренная часть, этот результат не распространяется на проектную врезку за её границей. Предел самостоятельной проверки построенной части задаёт [[Wiki/specifications/surveyed_part_publishable|проверка исполнительной съёмки]]. При последующем изменении смежного узла вопрос об объёме повторной проверки остаётся открытым в NET-06. [[Wiki/_registry/questions|Реестр вопросов]].

Основание в исходной модели. [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
