---
title: Operational Utility GIS
type: concept
status: draft
created: 2026-06-14
updated: 2026-06-20
source: "RAW_inputs/documents/UtilityGisEditor.md; RAW_inputs/documents/UtilityGisEditorRole.md"
tags: [concept, utility-gis, authoritative-editing, field-work, integrations]
---

# Operational Utility GIS

## Определение

`Operational Utility GIS` - справочная рыночная категория, объединяющая
authoritative network editing, исполнение полевых работ и интеграции
эксплуатационного контура.

Нода описывает соседний рынок и не определяет направление GeoService.

## Три Модуля

| Модуль | Ответственность |
|---|---|
| `Authoritative Network Editor` | versioning, topology, QA/QC, templates, approvals и controlled publication |
| `Field Work Execution` | offline mobile, inspections, photos, attachments, work packages, outage/damage и as-built |
| `Integration and Compliance Hub` | API/OGC/REST, EAM/ERP/OMS/ADMS, AD/SSO, audit, export и reports |

## Пользователи

- GIS editors и data stewards;
- field crews;
- dispatch, operations и emergency teams;
- designers и contractors;
- IT, security и integration teams.

## Отличие От Generic GIS Editor

Generic editor управляет features и attributes. `Operational Utility GIS`
дополнительно отвечает за physical/logical network state, topology,
connectivity, operational work context, evidence, controlled publication и
downstream integrations.

## Граница Применения

Категория используется только как vocabulary для анализа альтернатив. Она не
заменяет активный scope:

- Release 1 остается local focused conflict/review demo;
- electric `synthetic_utility_feeder_01` остается единственным demo-domain;
- offline mobile, production topology и enterprise integrations остаются за
границей текущего релиза.

Исследование рынка не меняет Release 1, Release 2 или roadmap.

## Практические Стеки И Боли

Role research добавляет две устойчивые практические архитектуры:

- `ArcGIS Pro + ArcGIS Enterprise + Utility Network + branch versioning` для
  governed versioned editing, conflicts, protected `Default` и web feature
  layers;
- `QGIS + PostGIS + QField/QFieldCloud`, а для water/wastewater -
  `GISwater + EPANET/SWMM`, где важны field sync, GeoPackage/PostGIS round-trip,
  SQL/Python automation и import cleanup.

Повторяющиеся боли operational utility GIS: version conflicts, dirty topology,
mobile sync/data loss, office/field divergence, PostGIS/client setup и
качество входных данных.

## Источники

- `RAW_inputs/documents/UtilityGisEditor.md`
- `RAW_inputs/documents/UtilityGisEditorRole.md`

## Связи

- [[../chats/2026-06-14-utility-gis-editor-market-research]]
- [[../chats/2026-06-20-utility-gis-editor-role-research]]
- [[../entities/competitors/utility_gis_editor_market_landscape]]
- [[utility_gis_editing_domain]]
- [[../index]]
