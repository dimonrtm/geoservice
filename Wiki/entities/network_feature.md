---
title: Network Feature
type: entity
status: active
created: 2026-06-24
updated: 2026-06-28
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md"
tags: [domain-knowledge, entity, utility-network]
confidence: high
related: [Wiki/entities/feeder, Wiki/entities/network_association, DDD_Wiki/bounded_contexts/utility_network]
---

# Network Feature

## Identity

`NetworkFeature` имеет стабильный `id` и `assetCode`, уникальный в пределах dataset.

## Lifecycle

В рабочей версии может быть прочитан, изменен, включен в change set и затем опубликован в authoritative state.

## Responsibilities

Представляет пространственный объект инженерной сети: junction, line, device или другой feature type.

Для first persisted edit slice разрешена только существующая line feature и только geometry diff, предпочтительно сдвиг внутренней вершины без изменения endpoints.

## Relationships

Связан с `Feeder`, `NetworkAssociation`, `AOI`, workspace filtering и `EditVersion`.
