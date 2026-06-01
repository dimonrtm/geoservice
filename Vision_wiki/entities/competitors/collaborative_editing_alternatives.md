---
title: Альтернативы Для Collaborative Editing Геометрии
type: entity
status: draft
created: 2026-06-01
updated: 2026-06-01
source: RAW_inputs/documents/Ф2.md
tags: [competitors, alternatives, collaborative-editing, research]
---

# Альтернативы Для Collaborative Editing Геометрии

## Статус

Нода фиксирует research-карту альтернатив для будущей Ф3. Vendor-specific утверждения требуют независимой проверки по доступным URL.

## Карта Альтернатив

| Альтернатива | Research-Фокус | Что Сравнить На Ф3 |
|---|---|---|
| ArcGIS Online | Общий operational layer, editor tracking, views и доступы | Как обнаруживаются и объясняются конкурирующие правки |
| ArcGIS Enterprise | Branch versioning, reconcile/post, controlled review | Цена и сложность explicit conflict workflow |
| Mergin Maps | GeoPackage diff/merge, local copies, conflict files | Offline sync UX и handling schema changes |
| QFieldCloud | Delta-sync, versioned files, роли, offline/direct access | Защита от overwrite и требования к stable keys |
| HOT Tasking Manager + OpenStreetMap | Task partitioning и validation | Организационное снижение overlap без тяжелых версий |
| MapStore + GeoServer | Self-hosted WFS-T, security rules, AOI/write filters | On-premises контроль и ограничения conflict UX |

## Ограничения

- Research не доказывает наличие рыночного спроса на GeoService.
- Citation-маркеры исходника непрозрачны вне исходной research-сессии.
- Альтернативы нужно сравнивать относительно выбранного primary scenario, а не абстрактно.

## Источники

- `RAW_inputs/documents/Ф2.md`

## Связи

- [[../../concepts/collaborative_editing_models]]
- [[../../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../../decisions/followups/index]]
