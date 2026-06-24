---
title: Network Association
type: entity
status: active
created: 2026-06-24
updated: 2026-06-24
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md"
tags: [domain-knowledge, entity, utility-network, association]
confidence: high
related: [Wiki/entities/network_feature, Wiki/entities/feeder, DDD_Wiki/bounded_contexts/utility_network]
---

# Network Association

## Identity

`NetworkAssociation` имеет стабильный `id`, `fromFeatureId`, `toFeatureId` и `associationType`.

## Lifecycle

Association входит в workspace только если оба endpoint feature попали в рабочую область.

## Responsibilities

Представляет nonspatial направленную связь между двумя `NetworkFeature`: connectivity, containment или attachment.

## Invariants

Association не ссылается на отсутствующий feature, а оба endpoint принадлежат тому же `Feeder`, что и association.
