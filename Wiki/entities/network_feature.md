---
title: Network Feature
type: entity
status: active
created: 2026-06-24
updated: 2026-07-25
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/first_save_for_edit_version.md"
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

Для непустого first persisted change set разрешена только одна существующая line feature и только сдвиг ровно одной внутренней вершины без изменения endpoints, остальных координат, vertex/part count, identity, attributes и associations. Equality с baseline используется для revert/no-op. Identity внутренней вершины в этом slice задается позицией в immutable baseline coordinate array.

## Relationships

Связан с `Feeder`, `NetworkAssociation`, `AOI`, workspace filtering и `EditVersion`.
