---
title: Generic Map Editing Subdomain
type: subdomain
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; Code_wiki/архитектура/api_and_realtime.md"
tags: [domain-knowledge, ddd, subdomain, generic]
confidence: high
related: [DDD_Wiki/domains/geoservice, DDD_Wiki/bounded_contexts/utility_network]
---

# Generic Map Editing Subdomain

## Classification

Generic/supporting subdomain. Существующие Layer/Feature CRUD, bbox, optimistic `version`/`409`, WebSocket realtime и MapLibre map foundation - полезная инфраструктура, но не главный пользовательский сценарий Release 1.

## Business Capability

Читать и отображать geospatial features, предоставлять низкоуровневые примитивы feature editing и realtime refresh для map layers.

## Boundary

Generic map editing не должен переопределять authoritative utility workflow или обходить инварианты `WorkOrder`, `EditVersion` и post.
