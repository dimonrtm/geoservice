---
title: Utility GIS Editor Role Research
type: session
status: active
created: 2026-06-20
updated: 2026-06-20
source: RAW_inputs/documents/UtilityGisEditorRole.md
tags: [research, utility-gis-editor, persona, role, operational-utility-gis, field-sync]
---

# Utility GIS Editor Role Research

## Контекст

`RAW_inputs/documents/UtilityGisEditorRole.md` - research source о том, как
пользователи, близкие к роли `Utility GIS editor`, реально работают в
authoritative utility network editing. Источник опирается на vendor docs,
GitHub/issues, форумы, блоги и success stories. Он не является direct user
interview и не закрывает external validation для GeoService.

## Главные Тезисы

- Роль ближе к `owner/editor of authoritative utility network changes`, а не к
  обычному редактору карты.
- В публичных источниках точная строка `UtilityGisEditor` почти не используется;
  близкие названия - `GIS editor`, `utility network editor`, `manager`,
  `fieldworker`, `hydraulics technician`, `MIS specialist`.
- Повседневная работа группируется в пять блоков: редактирование активов и
  атрибутов, topology/rules QA, trace/isolation, field package/sync,
  интеграции с operational systems и документами.
- Два заметных стека: `ArcGIS Pro + ArcGIS Enterprise + Utility Network +
  branch versioning` и `QGIS + PostGIS + QField/QFieldCloud`, для water -
  `GISwater + EPANET/SWMM`.
- Повторяющиеся боли: version conflicts, dirty areas после правок, rule и
  connectivity errors, мобильный sync/data loss, office/field divergence,
  PostGIS/client setup, импорт INP/SHP и подготовка данных к network rules.
- Для обучения роль лучше делить на три потока: core editing discipline,
  change governance и field/integration operations.
- KPI роли лучше привязывать к quality of publication: validate pass rate,
  time from field change to master publication, unresolved conflicts, repeated
  dirty areas, successful sync/package delivery и completeness of required
  attributes/attachments.

## Значение Для GeoService

Источник усиливает уже принятую рамку: GeoService проверяет не generic map
editing, а управляемое изменение authoritative network model. Он также
поддерживает акцент Release 1/2 на validation, reconcile/post, conflict review,
audit, field/as-built evidence и office/field context.

Источник добавляет важное ограничение: broad-domain applicability остается
гипотезой. Water/wastewater, electric, gas, telecom и mixed utilities имеют
разные domain operations и tooling, поэтому Release 1 должен оставаться
electric demo на `synthetic_utility_feeder_01`, а multi-utility claims требуют
отдельной проверки.

## Follow-up

- Проверить с реальными представителями роли, соответствует ли описание
  `owner/editor of authoritative utility network changes` их рабочей практике.
- Перед внешним использованием проверить официальные URL/version scope для
  `QField`, `QFieldCloud`, `GISwater`, `EPANET/SWMM`, `PostGIS`,
  `ArcGIS Utility Network` и связанных claims.
- Не превращать source в обещание поддержки water/gas/telecom в текущем
  Release 1.

## Связи

- [[../entities/personas/utility_gis_editor]]
- [[../concepts/utility_gis_editing_domain]]
- [[../concepts/operational_utility_gis]]
- [[../concepts/jtbd]]
- [[../entities/competitors/utility_gis_editor_market_landscape]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
