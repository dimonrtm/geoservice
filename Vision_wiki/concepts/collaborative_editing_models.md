---
title: Модели Collaborative Editing Геометрии
type: concept
status: draft
created: 2026-06-01
updated: 2026-06-01
source: RAW_inputs/documents/Ф2.md
tags: [concept, collaborative-editing, geometry, research]
---

# Модели Collaborative Editing Геометрии

## Определение

Collaborative editing геометрии не сводится к одной функции. Research для Ф2-Ф3 выделяет четыре модели, рассчитанные на разные классы риска и рабочие контексты.

## Модели

| Модель | Контекст | Основной Риск | Примеры Из Research |
|---|---|---|---|
| Общий live-layer | Быстрые operational updates несколькими редакторами | Silent overwrite, недостаточная прозрачность последних изменений | ArcGIS Online |
| Изолированные версии | Authoritative layers, long transactions, review перед публикацией | Конфликты при reconcile/post, сложность контролируемого merge | ArcGIS Enterprise |
| Локальные копии и sync/merge | Полевые и offline workflows | Overwrite, schema drift, ошибки ключей, потеря несинхронизированных правок | Mergin Maps, QFieldCloud |
| Task partitioning и validation | Массовая распределенная редактура | Overlap зон, upload conflicts, неоднородное качество | HOT Tasking Manager + OpenStreetMap |

Self-hosted MapStore + GeoServer показывает дополнительный акцент: предотвращение конфликтов через role-scoped и AOI-scoped editing, write filters и транзакционную запись.

## Гипотезы Для GeoService

- `optimistic concurrency` Release 1 покрывает только часть модели общего live-layer.
- Audit trail, визуальное объяснение конфликта, soft-reservation, workspace mode, reviewer workflow, AOI scopes и offline sync требуют отдельной приоритизации на Ф4.
- Product scope нельзя расширять автоматически только на основании research.

## Неясно

- Primary research-persona `Utility GIS editor` соответствует модели изолированных версий и контролируемой публикации authoritative state.
- Неясно, должен ли Release 1 оставаться только demo live-layer сценарием или проверять часть более сложной модели: решение относится к Ф4.

## Источники

- `RAW_inputs/documents/Ф2.md`

## Связи

- [[../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../entities/personas/collaborative_editing_archetypes]]
- [[../entities/competitors/collaborative_editing_alternatives]]
- [[../solution/USM]]
