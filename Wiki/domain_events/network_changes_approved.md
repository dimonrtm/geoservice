---
title: "Изменения сети утверждены"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/commands/approve_network_changes, Wiki/commands/publish_network_changes]
---

# Изменения сети утверждены

## Source Aggregate

[[DDD_Wiki/aggregates/network_edit_version|Рабочая версия сети]] учитывает решение по предъявленному объёму.

## Happened In The Past

В рабочей версии принято решение об утверждении определённого проверенного объёма. Можно установить, какие правки рассмотрел уполномоченный участник и к какому объёму относится решение.

## Downstream Reactions

Публикующий получает основание для внесения именно этих изменений в официальный слой. Утверждённая версия может ещё ожидать публикации. Вопрос о последствиях последующей смежной правки выделен в NET-06. [[Wiki/_registry/questions|Открытые вопросы]].

Основание в исходной модели. [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
