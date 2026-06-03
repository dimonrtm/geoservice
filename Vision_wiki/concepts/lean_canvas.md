---
title: Lean Canvas GeoService
type: concept
status: draft
created: 2026-05-31
updated: 2026-06-03
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md; RAW_inputs/documents/03.06.2026deep-research-report.md"
tags: [lean-canvas, discovery, research]
---

# Lean Canvas GeoService

## Problem

- Подтверждено: требуется исследовать возможности реализации алгоритмов совместного редактирования геометрии.
- Гипотеза Ф2: utility-организациям нужен контролируемый способ совместного изменения authoritative network layer без silent overwrite и неверного состояния сети.

## Customer Segments

- Подтверждено: разработчик проекта как исследователь и первый пользователь.
- Гипотеза Ф2: primary research-persona - `Utility GIS editor`. Кадастровый инженер остается deferred research-сценарием.

## Unique Value Proposition

- Гипотеза Ф3: GeoService не конкурирует как новая mature GIS platform, а показывает conflict/review layer, который делает сложный utility conflict когнитивно проще для reviewer'а и помогает доказать безопасность authoritative post.

## Solution

- Текущий technical demo draft описан в [[../solution/USM]].
- Не фиксировать окончательный scope до Ф4.
- Demo-кандидат после Ф3: `geometry/association conflict` с dirty areas, network consequence, reviewer decision и итоговым authoritative state.

## Channels

- GitHub, demo и portfolio.
- Возможное применение в реальной работе требует отдельной проверки.

## Revenue / Value

- Исследовательская ценность: изучение методов collaborative editing геометрии.
- Инженерная ценность: проверка AI-first разработки сложной геоинформационной системы.
- Возможная продуктовая ценность пока является гипотезой.

## Cost / Constraints

- Pet-проект развивается одним разработчиком.
- При отсутствии четкого demo-script есть риск оставить незавершенный репозиторий.

## Key Metrics

- Пока не определены. Нужен проверяемый критерий готовности первого релиза.

## Unfair Advantage

- Гипотеза Ф3: focused demo, self-hosted/local mode, open-source posture и AI-first объяснение конфликта для reviewer'а. Это преимущество работает только в узкой нише explainability/review productivity, а не в замене ArcGIS Enterprise.
