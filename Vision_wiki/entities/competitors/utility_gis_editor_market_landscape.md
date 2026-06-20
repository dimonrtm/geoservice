---
title: Рыночный Ландшафт Utility GIS Editor
type: entity
status: draft
created: 2026-06-14
updated: 2026-06-20
source: "RAW_inputs/documents/UtilityGisEditor.md; RAW_inputs/meetings/geometry_association_conflict_f3.md; RAW_inputs/documents/UtilityGisEditorRole.md"
tags: [competitors, utility-gis-editor, market, international, russian]
---

# Рыночный Ландшафт Utility GIS Editor

## Статус

Research-карта расширяет существующее сравнение collaborative editing
платформ специализированными utility, field и asset/work systems.

Vendor claims извлечены из RAW source и не перепроверены в рамках ingest.
Перед внешним сравнением нужны актуальные официальные URL, version scope,
deployment, pricing и licensing.

## Семейства Решений

| Семейство | Референсы | Сильная Сторона |
|---|---|---|
| Network design и digital twin | Bentley OpenUtilities, IQGeo | authoritative network model, design/as-built, utility workflows и integrations |
| Telecom/utility editing и field execution | 3-GIS, OSPInsight | inventory, redlining, inspections, work orders и field-office sync |
| Asset/work management | Trimble Cityworks | GIS-centric inspections, maintenance и work execution |
| CAD/GIS bridge | Autodesk Map 3D | enterprise geodata внутри CAD-centric engineering workflow |
| Open domain platform | GISwater | water/wastewater model, simulations и open-source ecosystem |
| Lightweight field/offline | Mappt | mobile collection, photos, forms и offline work |
| Open-source field/office utility practice | QGIS, PostGIS, QField/QFieldCloud, GISwater, EPANET/SWMM | field package/sync, GeoPackage/PostGIS round-trip, water/wastewater modeling, SQL/Python automation и import cleanup |

## Русскоязычный Сегмент

| Референс | Исследовательский Вывод |
|---|---|
| Политерм `ZuluGIS` | Наиболее прямое сочетание network editor, web/mobile и domain calculations |
| NextGIS | Platform-oriented фундамент: QGIS, on-prem, API, permissions и field collection |
| КБ «Панорама» | Корпоративный server/web stack и OGC interfaces |
| СКАНЭКС GeoMixer | Интеграционная web-GIS платформа с editing и API |
| ИндорСофт | Локализованные domain products, включая power и field tooling |

## Значение Для GeoService

- Главный incumbent baseline остается `ArcGIS Enterprise + Utility Network`.
- Полный рынок намного шире conflict explanation и включает field execution,
  work management, calculations и integrations.
- GeoService пока может отличаться только focused explainability/review
  experience; преимущество перед зрелыми platforms не доказано.
- Локальные vendors расширяют справочный контекст по on-prem, integration и
  domain capabilities; выводов об изменении demo scope из этого не следует.
- Ф3 `geometry/association conflict` уточняет, что adjacent suites уровня
  Cityworks/Bentley и generic self-hosted platform конкурируют как work context,
  governance, history/API или internal-dashboard foundation, но их наличие не
  доказывает semantic reviewer decision для authoritative utility-network
  conflict.
- Role research уточняет, что для многих real-world workflows конкурентом
  является не один продукт, а stack из GIS editor, field client, PostGIS,
  scripts, domain tooling и operational integrations.

## Ограничения

- Citation-маркеры источника непрозрачны вне исходной research-сессии.
- Некоторые URLs даны без protocol и требуют проверки.
- Capability и commercial claims могут изменяться между версиями.
- Сравнение не является vendor due diligence.
- Публичная доказательная база по точному названию `UtilityGisEditor` слабая;
  выводы привязаны к функции роли и adjacent titles.
- Claims о том, что adjacent suites закрывают именно `geometry/association
  conflict` consequence review, требуют отдельного официального подтверждения.

## Связи

- [[../../chats/2026-06-14-utility-gis-editor-market-research]]
- [[../../chats/2026-06-19-geometry-association-conflict-f3]]
- [[../../chats/2026-06-20-utility-gis-editor-role-research]]
- [[../../concepts/operational_utility_gis]]
- [[collaborative_editing_alternatives]]
- [[../../decisions/followups/index]]
