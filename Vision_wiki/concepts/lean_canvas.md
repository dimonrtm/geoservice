---
title: Lean Canvas GeoService
type: concept
status: draft
created: 2026-05-31
updated: 2026-06-05
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md; RAW_inputs/documents/03.06.2026deep-research-report.md; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md"
tags: [lean-canvas, discovery, research]
---

# Lean Canvas GeoService

## Problem

- Подтверждено: требуется исследовать возможности реализации алгоритмов совместного редактирования геометрии.
- Гипотеза Ф2: utility-организациям нужен контролируемый способ совместного изменения authoritative network layer без silent overwrite и неверного состояния сети.

## Customer Segments

- Подтверждено: разработчик проекта как исследователь и первый пользователь.
- Ф5 rollout audience: разработчик, смотрящий локальное demo.
- Гипотеза Ф2: primary research-persona - `Utility GIS editor`. Кадастровый инженер остается deferred research-сценарием.

## Unique Value Proposition

- Гипотеза Ф3: GeoService не конкурирует как новая mature GIS platform, а показывает conflict/review layer, который делает сложный utility conflict когнитивно проще для reviewer'а и помогает доказать безопасность authoritative post.

## Solution

- Текущий technical demo draft описан в [[../solution/USM]].
- Ф4 scope: demo focused conflict/review layer для `Utility GIS editor`.
- Primary demo-сценарий: `geometry/association conflict` с dirty areas, network consequence, reviewer decision и итоговым authoritative state.
- В MVP входят conflict explanation и reviewer decision.
- `edit after reconcile` переносится в Next/Later.

## Channels

- GitHub, demo и portfolio.
- Первый rollout: local Docker Compose demo для владельца pet-проекта / разработчика.
- Возможное применение в реальной работе требует отдельной проверки.

## Revenue / Value

- Исследовательская ценность: изучение методов collaborative editing геометрии.
- Инженерная ценность: проверка AI-first разработки сложной геоинформационной системы.
- Ф5 ценность первого rollout: `learning value`; показать на demo, что pipeline действительно стал проще.
- Возможная продуктовая ценность пока является гипотезой.

## Cost / Constraints

- Pet-проект развивается одним разработчиком.
- При отсутствии четкого demo-script есть риск оставить незавершенный репозиторий.
- Ф5 constraints: запуск только локально через Docker Compose; demo использует synthetic dataset; нужны `PostGIS seed`, `auth`, `import GeoJSON`; не нужны external GIS, `ArcGIS`/`QGIS` export и CI demo data reset.

## Key Metrics

- Demo готов, если параллельная правка инженерной сети не теряется молча, а reviewer видит объяснение конфликта и принимает явное решение перед publication в authoritative state.
- Ф5 rollout готов, если developer может локально пройти `Editor flow` по README/demo script и увидеть, что pipeline сетевой правки стал понятнее.

## Unfair Advantage

- Гипотеза Ф3: focused demo, self-hosted/local mode, open-source posture и AI-first объяснение конфликта для reviewer'а. Это преимущество работает только в узкой нише explainability/review productivity, а не в замене ArcGIS Enterprise.
