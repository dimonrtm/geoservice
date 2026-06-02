---
title: Risk And Assumption Log
type: risk
status: active
created: 2026-05-31
updated: 2026-06-02
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; RAW_inputs/documents/Ф2.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md"
tags: [risk, assumption, discovery]
---

# Risk And Assumption Log

## Допущения

| ID | Статус | Допущение | Как Проверить |
|---|---|---|---|
| AS-2026-05-31-001 | hypothesis | Совместное редактирование геометрии является полезной задачей не только для учебного pet-проекта. | На Ф2 описать конкретного пользователя и сценарий; позже проверить на реальном рабочем контексте. |
| AS-2026-05-31-002 | hypothesis | GeoService может стать основой demo, portfolio, применения в работе или будущего продукта. | Уточнить приоритет результата и критерий готовности первого релиза. |
| AS-2026-05-31-003 | hypothesis | AI-first разработка подходит для создания сложной геоинформационной системы. | Фиксировать ограничения, качество реализации и стоимость исправлений по мере развития проекта. |
| AS-2026-06-01-001 | hypothesis | Для проверки GeoService достаточно выбрать один primary scenario collaborative editing и воспроизвести канонические конфликты на synthetic dataset. | Для `Utility GIS editor` подготовить synthetic utility dataset и проверить topology, `attribute vs attribute`, `geometry/association`, `edit after reconcile`. |
| AS-2026-06-02-001 | hypothesis | Наиболее релевантный primary scenario GeoService - authoritative editing для `Utility GIS editor`. | Проверить модельную боль на synthetic utility dataset и, если возможно, на реальном рабочем контексте. |

## Риски

| ID | Статус | Риск | Влияние | Снижение Риска |
|---|---|---|---|---|
| RK-2026-05-31-001 | open | Цель первого релиза сформулирована как "все типа работает" и пока не проверяема. | Невозможно однозначно завершить релиз или оценить результат исследования. | На Ф2-Ф4 сформулировать demo-script и acceptance criteria. |
| RK-2026-05-31-002 | open | Проект может остаться незавершенным репозиторием на GitHub. | Исследовательская и portfolio-ценность не материализуются. | Выбрать минимальный demonstrable результат первого релиза. |
| RK-2026-06-01-001 | open | Research перечисляет много полезных capabilities, а выбранный utility-сценарий сам по себе сложнее Release 1. | Scope GeoService может преждевременно разрастись до branch mode, reviewer workflow и topology validation. | До Ф4 не считать research-рекомендации требованиями; Release 1 не расширять автоматически. |

## Связи

- [[../chats/2026-05-31-phase-f1-why-now]]
- [[../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../concepts/jtbd]]
- [[../concepts/product_vision_board]]
- [[../concepts/lean_canvas]]
- [[followups/index]]
