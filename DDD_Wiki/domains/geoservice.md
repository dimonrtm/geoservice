---
title: GeoService Domain
type: domain
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; RAW_inputs/documents/utility_gis_editor_domain_dictionary.md"
tags: [domain-knowledge, ddd, domain]
confidence: high
related: [DDD_Wiki/subdomains/utility_authoritative_editing, Wiki/glossary/utility_gis_editing]
---

# GeoService Domain

GeoService исследует управляемое редактирование данных инженерной сети. Главный домен текущего release - безопасное изменение authoritative utility network state через `WorkOrder`, isolated `EditVersion`, validation, reconcile, review, post и audit.

## Business Capability

Дать пользователю путь от назначенной `WorkOrder` до проверенного изменения сети без silent overwrite и без прямой правки authoritative `Default`.

## Boundaries

Generic GIS CRUD, загрузка layer bbox, рендеринг MapLibre и raw feature WebSocket остаются техническим основанием, а не отдельным продуктовым сценарием.
