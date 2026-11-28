---
title: "Изменения включены в официальную сеть"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/commands/publish_network_changes, Wiki/system_events/published_changes_received]
---

# Изменения включены в официальную сеть

## Source Aggregate

[[DDD_Wiki/aggregates/network_edit_version|Рабочая версия сети]] фиксирует опубликованный объём. Официальная схема отражает результат.

## Happened In The Past

Утверждённые изменения определённого объёма рабочей версии внесены в официальный слой. С этого момента записи активов и соединения в нём отражают опубликованный результат. История версии связывает его с подготовленной правкой.

## Downstream Reactions

Офисные пользователи работают с новым официальным состоянием. Результат доступен для синхронизации с полем и внешними системами. Когда конкретный потребитель получил обновление, устанавливают по обмену с ним. [[Wiki/system_events/published_changes_received|Получение обновления потребителем]].

Основание в исходной модели. [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
