---
title: Research Для Ф2-Ф3 По Collaborative Editing
type: session
status: active
created: 2026-06-01
updated: 2026-06-01
source: RAW_inputs/documents/Ф2.md
tags: [research, discovery, phase-f2, phase-f3, collaborative-editing]
---

# Research Для Ф2-Ф3 По Collaborative Editing

## Контекст

`RAW_inputs/documents/Ф2.md` содержит сравнительный обзор веб-ГИС сервисов и экосистем collaborative editing. Это не ответы стейкхолдера и не подтверждение primary user GeoService. Материал используется как research для подготовки Ф2-Ф3.

Источник рассматривает:

- ArcGIS Online;
- ArcGIS Enterprise;
- Mergin Maps;
- QFieldCloud;
- HOT Tasking Manager + OpenStreetMap;
- MapStore + GeoServer.

## Что Извлечено

- Выделены четыре устойчивые модели collaborative editing: общий live-layer, изолированные версии, локальные копии с sync/merge и task partitioning с validation.
- Описаны семь вымышленных, но реалистичных пользовательских архетипов.
- Для каждого сценария перечислены конфликтные ситуации, последствия, обходные пути и возможный synthetic pilot.
- В выводах источника предложены product capabilities. До Ф4 они являются гипотезами, а не утвержденным scope GeoService.

## Ограничения Источника

- Персоны и оценки частоты сценариев являются аналитическими архетипами, а не данными реальных клиентов GeoService.
- Citation-маркеры вида `turn10view7` не являются переносимыми URL. Vendor-specific утверждения нельзя считать независимо проверенными до добавления доступных ссылок или исходного списка источников.
- Материал частично питает Ф3, хотя файл назван `Ф2.md`.

## Следующие Шаги

1. Выбрать один primary scenario для GeoService или явно оставить несколько сценариев для сравнения.
2. Проверить выбранный сценарий на реальном рабочем контексте или synthetic dataset.
3. Запросить доступный список ссылок для vendor-specific утверждений.
4. На Ф4 решить, какие capabilities входят в Release 1, а какие остаются Later.

## Связи

- [[../concepts/collaborative_editing_models]]
- [[../entities/personas/collaborative_editing_archetypes]]
- [[../entities/competitors/collaborative_editing_alternatives]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
