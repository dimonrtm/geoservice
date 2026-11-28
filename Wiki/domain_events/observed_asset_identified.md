---
title: "Установлена принадлежность наблюдения активу"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/field_observation, Wiki/commands/identify_observed_asset, Wiki/specifications/observation_identifies_asset]
---

# Установлена принадлежность наблюдения активу

## Source Aggregate

[[DDD_Wiki/aggregates/field_observation|Полевое наблюдение]] хранит установленную принадлежность и основание выбора.

## Happened In The Past

ГИС-редактор связал конкретное наблюдение по наряду с одним активом и сохранил различающее основание. Ранее у наблюдения могли оставаться две возможные задвижки. Опознание одной из них устраняет неоднозначность именно для этого наблюдения.

## Downstream Reactions

Редактор может теперь сравнить его замер с координатами установленного актива либо добавить относящийся к нему осмотр. Для выбора геометрии он ещё проверяет сопоставимость и качество измерений. Другие наблюдения из пакета сохраняют собственный результат идентификации.

Решения условной организации через `expert_repson`. [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
