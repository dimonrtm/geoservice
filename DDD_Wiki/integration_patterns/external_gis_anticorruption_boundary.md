---
title: External GIS Anti-Corruption Boundary
type: integration-pattern
status: planned
created: 2026-06-24
updated: 2026-06-26
source: "RAW_inputs/documents/UtilityGisEditorRole.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, ddd, integration-pattern, acl]
confidence: medium
related: [DDD_Wiki/bounded_contexts/review_post, DDD_Wiki/context_map/geoservice_context_map]
---

# External GIS Anti-Corruption Boundary

## Pattern

GeoService не должен дословно копировать external GIS conflict/editor semantics. Release 2 позиционирует consequence package как decision support поверх native conflict workflow, а не как замену conflict editor или topology engine.

## Protected Language

Внутренние термины `approve package`, `can_post`, `stale approval`, `absolute veto`, `RiskTier` и `post-gate` защищают модель GeoService от сведения к visual diff `Base/Mine/Default`.

## Open Questions

Implementation contract должен определить, какие external GIS data импортируются как evidence, а какие остаются за пределами bounded context.
