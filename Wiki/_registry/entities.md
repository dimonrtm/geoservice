---
title: Entities Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, entity]
confidence: n/a
related: [Wiki/index]
---

# Entities Registry

| Entity | Identity | Aggregate | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/entities/work_order]] | `id`, `code` | [[DDD_Wiki/aggregates/work_order]] | high | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md` |
| [[Wiki/entities/edit_version]] | `id`, `workOrderId`, `baseNetworkRevision` | [[DDD_Wiki/aggregates/edit_version]] | high | `Code_wiki/архитектура/data_model.md` |
| [[Wiki/entities/default_state]] | `WorkOrder` + `baseNetworkRevision` | [[DDD_Wiki/aggregates/work_order]] | high | `Code_wiki/архитектура/data_model.md` |
| [[Wiki/entities/feeder]] | `id`, `code` | Граница utility network / work order | high | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md` |
| [[Wiki/entities/network_feature]] | `id`, `assetCode` | Utility network | high | `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md` |
| [[Wiki/entities/network_association]] | `id`, endpoints, type | Utility network | high | `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md` |
| [[Wiki/entities/review_decision]] | package id + actor + timestamp | [[DDD_Wiki/aggregates/review_package]] | medium | `Vision_wiki/decisions/release_2_conflict_explanation.md` |
