---
title: Представление сети и эксплуатационное состояние
type: concept
status: active
created: 2026-10-18
updated: 2026-10-18
source: RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis.md
tags: [domain-knowledge, research, simulated-organization]
confidence: high
related: [Wiki/policies/network_edit_semantics_policy, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Представление сети и эксплуатационное состояние

## Различаемые предметы

Геометрия представления, идентичность физического актива, отношения сети, жизненный цикл, эксплуатационное состояние и расчётный сценарий описывают разные свойства. Равенство геометрии не означает равенства этих состояний.

## Внешние основания и новое знание

- GISwater Replace сохраняет topology, создавая замену старого объекта; virtual arc может выражать связь без физической трубы. Это примеры отдельных доменных операций. [O14 — Replace feature](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/replace-feature.html) [O08 — Data model for Giswater](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/data-model-giswater.html)
- Containment и attachment не являются каналом ресурса; split контейнера не обязан разделять содержимое. Unlocatable objects могут выпадать из dirty-area проверки. [E16 — Containment associations](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/containment.html) [E17 — Junction and edge objects](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/nonspatial-objects.html) [E18 — Structural attachment associations](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/structural-attachments.html)
- Connected trace не удостоверяет traversability, а достижимость не доказывает достаточный расход. [E26 — Connectivity and traversability](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/connectivity-and-traversability.html) [D17 — US EPA — WNTR User Manual](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1012G9B.TXT)
- Состояния клапанов меняют качество работы без изменения координат. Сценарные параметры и результаты расчёта отделяются от inventory. [D24 — US EPA — Water Age Management](https://www.epa.gov/system/files/documents/2022-04/ds-toolbox-fact-sheets_water-age-mgt_final-508_revised.pdf) [O18 — Dynamic Scenarios Manager](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/dscenario-manager.html) [O20 — Result manager](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/result-manager.html)
- DMA/PRESSZONE могут определяться сетью и ограничителями; полигон — вариант изображения результата. Это иной смысл, чем AOI разрешённого редактирования. [O19 — Netscenarios](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/netscenarios.html)

## Применение в GeoService

Принято как правило интерпретации: называть предмет изменения и точное свойство проверки; не делать скрытых каскадных изменений, не считать Save доказательством эксплуатационной готовности. Область QA включает не только географический extent, но и классы объектов, конфигурацию и состояние источников. Отсутствие найденных ошибок без известного охвата не доказывает полноту.

Новые commands замены активов, агрегаты сценариев, nonspatial storage и hydraulic engine не вводятся. Эти возможности требуют отдельных задач. Действующая политика [[Wiki/policies/network_edit_semantics_policy]] и инварианты [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] сохраняются.
