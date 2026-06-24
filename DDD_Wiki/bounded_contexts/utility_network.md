---
title: Utility Network Context
type: bounded-context
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, ddd, bounded-context, utility-network]
confidence: high
related: [Wiki/entities/feeder, Wiki/entities/network_feature, Wiki/entities/network_association]
---

# Utility Network Context

## Ubiquitous Language Boundary

Внутри контекста `Feeder`, `NetworkFeature`, `NetworkAssociation`, `NetworkState`, `Default` и `baseNetworkRevision` описывают актуальную инженерную сеть и baseline snapshots.

## Model Ownership

Контекст владеет feeder graph, features, associations и network revision. Он не владеет `AOI`.

## Interfaces

Предоставляет feeder aggregate и snapshots в [[DDD_Wiki/bounded_contexts/work_order]]. Future validation/trace semantics могут стать отдельным контекстом, если появится topology engine.
