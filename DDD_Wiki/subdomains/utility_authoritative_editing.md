---
title: Utility Authoritative Editing Subdomain
type: subdomain
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; Vision_wiki/concepts/utility_gis_editing_domain.md"
tags: [domain-knowledge, ddd, subdomain, core]
confidence: high
related: [Wiki/glossary/utility_gis_editing, DDD_Wiki/bounded_contexts/work_order, DDD_Wiki/bounded_contexts/review_post]
---

# Utility Authoritative Editing Subdomain

## Classification

Core subdomain. Он определяет ценность GeoService: безопасный workflow изменения authoritative utility network state, а не просто отображение и CRUD геометрии.

## Business Capability

`WorkOrder` -> `EditVersion` -> editing -> validation -> reconcile -> conflict resolution -> review -> post -> audit.

## Related Contexts

[[DDD_Wiki/bounded_contexts/work_order]], [[DDD_Wiki/bounded_contexts/utility_network]], [[DDD_Wiki/bounded_contexts/review_post]], [[DDD_Wiki/bounded_contexts/audit]].
