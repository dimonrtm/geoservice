---
title: "Ребро разделено на сохранившейся трубе"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, DDD_Wiki/aggregates/network_asset, Wiki/commands/split_preserved_pipe_edge]
---

# Ребро разделено на сохранившейся трубе

## Source Aggregate

[[DDD_Wiki/aggregates/network_edit_version|Рабочая версия сети]] объединяет правку узла и смежных рёбер. [[DDD_Wiki/aggregates/network_asset|Физическая труба]] сохраняет историю осмотров.

## Happened In The Past

После установки задвижки редактор представил изменение в рабочей версии новым узлом и двумя рёбрами вместо прежнего. Для каждого нового ребра сохранена связь с одной и той же физической трубой. Это изменение позволяет проверять новые пути и впоследствии опубликовать новую связность.

## Downstream Reactions

Сотрудник, рассматривающий один из отрезков, может найти прежние осмотры трубы. Локальный вывод о дефекте он вправе отнести к отрезку лишь при установленных привязке и охвате. Появление двух рёбер сохраняет прежнее число наблюдений.

Решения условной организации через `expert_repson`. [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
