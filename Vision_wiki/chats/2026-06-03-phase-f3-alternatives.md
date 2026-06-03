---
title: Ф3 Альтернативы Для Utility GIS Editor
type: session
status: draft
created: 2026-06-03
updated: 2026-06-03
source: RAW_inputs/documents/03.06.2026deep-research-report.md
tags: [discovery, phase-f3, alternatives, utility-network, research]
---

# Ф3 Альтернативы Для Utility GIS Editor

## Контекст

Источник сравнивает GeoService с альтернативами для primary scenario `Utility GIS editor`: цепочка `edit -> reconcile -> review -> post -> доказуемо корректное authoritative state`.

Исходная база - предыдущий research `RAW_inputs/documents/Ф2.md`; новый документ переоценивает альтернативы относительно utility authoritative editing и отдельно помечает, какие claims требуют URL-перепроверки.

## Главные Тезисы

- Для полноценного authoritative utility editing главный baseline - `ArcGIS Enterprise + Utility Network + branch versioning`.
- ArcGIS Enterprise уже закрывает named versions, reconcile/post, protected default, conflict review, reviewer/admin gate, dirty areas и topology validation.
- ArcGIS Online подходит для controlled operational editing, но не является столь сильной основой для canonical utility network workflow.
- Mergin Maps и QFieldCloud сильны как offline/field workflows и синхронизация локальных копий, но слабее как authoritative post/review workflow.
- HOT Tasking Manager + OpenStreetMap полезен как reference pattern task partitioning и validation, но не replacement для utility source of truth.
- MapStore + GeoServer интересен как self-hosted/open-stack governance baseline, но слабее в наглядном conflict UX и utility-specific validation semantics.
- GeoService имеет шанс не как замена mature GIS platform, а как focused layer объяснения конфликтов, review-UX и доказуемости authoritative post.

## Критерии Выбора

Для utility-команды важнее всего:

1. Надежность authoritative state и доверие к trace/topology результатам.
2. Fit к существующему стеку и operational process.
3. Размещение, security и governance.
4. Audit/review trail.
5. Стоимость и скорость внедрения.

Типичные блокеры: `GIS lead`/data steward, network operations, IT/security, compliance и бюджетный владелец.

## Demo-Кандидат

Самый убедительный demo-сценарий GeoService - `geometry/association conflict`, который создает dirty areas и меняет сетевое последствие. Demo должен показать conflict explanation, reviewer decision и итоговое authoritative state после post или rejection.

## Follow-up

- Перепроверить URL-источниками non-Esri claims по Mergin Maps, QFieldCloud, HOT Tasking Manager/OpenStreetMap и MapStore/GeoServer.
- На Ф4 решить, остается ли GeoService focused conflict/review layer для demo или пытается проверять более широкий branch/versioning workflow.
- Для synthetic validation использовать `geometry/association conflict` как главный сценарий, `edit after reconcile` как второй сценарий.

## Связи

- [[../entities/competitors/collaborative_editing_alternatives]]
- [[../entities/personas/utility_gis_editor]]
- [[../concepts/lean_canvas]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
