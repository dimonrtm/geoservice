---
title: GeoService Context Map
type: context-map
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/data_model.md; Code_wiki/архитектура/api_and_realtime.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, ddd, context-map]
confidence: high
related: [DDD_Wiki/bounded_contexts/work_order, DDD_Wiki/bounded_contexts/utility_network, DDD_Wiki/bounded_contexts/review_post]
---

# GeoService Context Map

## Upstream Downstream

| Upstream | Downstream | Relationship |
| --- | --- | --- |
| Auth Context | Work Order Context | Auth поставляет active user и role; work order владеет assignment rules. |
| Utility Network Context | Work Order Context | Utility network поставляет feeder/default snapshots; work order владеет `AOI` и edit version workspace. |
| Work Order Context | Review Post Context | Work order/edit version поставляет package input; review/post владеет approval и post gate. |
| Review Post Context | Audit Context | Review/post публикует decisions, stale events и post outcomes. |

## Integration Pattern

Текущая реализация использует repositories application layer вместо cross-schema foreign keys между будущими service boundaries. Это осознанная anti-corruption boundary между persistence schemas и domain contexts.

## Risks

Граница между `Reviewer` и `Publisher` остается нерешенной; см. [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]].
