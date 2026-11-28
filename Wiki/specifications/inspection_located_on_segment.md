---
title: "Осмотр можно отнести к образованному отрезку трубы"
type: specification
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_asset, Wiki/value_objects/evidence_extent, Wiki/commands/split_preserved_pipe_edge]
---

# Осмотр можно отнести к образованному отрезку трубы

## Predicate

Для прежнего осмотра установлена идентичность сохранённой физической трубы. Записанные при осмотре привязка и охват позволяют поместить результат на конкретный отрезок после деления. Например, дефект с однозначным ориентиром на одной стороне новой задвижки виден на соответствующем ребре.

## Failure Meaning

Если указан лишь прежний объект целиком, дефект без локализации остаётся в его истории. Две ссылки новых рёбер на трубу сами по себе не подтверждают, что оба отрезка осмотрены или дефект обнаружен на каждом. При физической замене сначала заново проверяют идентичность актива.

Решения условной организации через `expert_repson`. [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
