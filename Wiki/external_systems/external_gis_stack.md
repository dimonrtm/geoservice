---
title: External GIS Stack
type: external-system
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "RAW_inputs/documents/UtilityGisEditorRole.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, external-system, gis]
confidence: medium
related: [DDD_Wiki/integration_patterns/external_gis_anticorruption_boundary, DDD_Wiki/context_map/geoservice_context_map]
---

# External GIS Stack

External GIS stack включает ArcGIS Utility Network, QGIS/QField, GISwater/PostGIS и соседние операционные системы, которые используются как evidence, baseline или точка сравнения для utility editing workflows.

## Integration Boundary

GeoService должен использовать внешние GIS-факты как evidence, но сохранять собственный язык для review package, stale approval, hard blockers и безопасности post.

## Open Questions

Какие интеграции нужны для developer demo, а какие остаются research context?
