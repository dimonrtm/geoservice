---
title: Risk And Assumption Log
type: risk
status: active
created: 2026-05-31
updated: 2026-06-04
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; RAW_inputs/documents/Ф2.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md; RAW_inputs/documents/03.06.2026deep-research-report.md; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md"
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
| AS-2026-06-03-001 | hypothesis | Узкая зона ценности GeoService - conflict explanation и review productivity, а не замена `ArcGIS Enterprise + Utility Network`. | На Ф4 сформулировать demo-script вокруг `geometry/association conflict`, dirty areas, reviewer decision и authoritative post. |
| AS-2026-06-04-001 | accepted-for-demo | Ф4 scope GeoService - demo focused conflict/review layer, где главный сигнал ценности: `review стал проще`. | Проверить через walking skeleton: work order -> working version -> change set -> validation -> compare with `Default` -> conflict explanation -> reviewer decision -> publish. |

## Риски

| ID                | Статус    | Риск                                                                                                                            | Влияние                                                                                                                                               | Снижение Риска                                                                                                                                                                        |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RK-2026-05-31-001 | mitigated | Цель первого релиза была сформулирована как "все типа работает"; Ф4 заменила ее на demo walking skeleton и acceptance criteria. | Риск снова появится, если критерии из `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` не будут сжаты в реализуемый Release 1 subset. | Держать главный критерий: ни одна параллельная правка инженерной сети не теряется молча.                                                                                              |
| RK-2026-05-31-002 | mitigated | Проект может остаться незавершенным репозиторием на GitHub.                                                                     | Исследовательская и portfolio-ценность не материализуются.                                                                                            | Ф4 выбрала минимальный demonstrable результат: demo, где `review стал проще`.                                                                                                         |
| RK-2026-06-01-001 | open      | Research перечисляет много полезных capabilities, а выбранный utility-сценарий сам по себе сложнее Release 1.                   | Scope GeoService может преждевременно разрастись до branch mode, reviewer workflow и topology validation.                                             | Ф4 non-goals: full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL, production utility network model. Scope creep сигнал - новые незапланированные на релиз фичи. |
| RK-2026-06-03-001 | mitigated | `ArcGIS Enterprise + Utility Network` уже является good-enough incumbent для полноценного authoritative utility editing.        | GeoService как продукт может быть не нужен, если не покажет сильное преимущество в explainability или review productivity.                            | Ф4 зафиксировала demo focused conflict/review layer, а не попытку заменить mature GIS platform.                                                                                       |
| RK-2026-06-03-002 | open      | Non-Esri vendor-specific claims из Ф3 research пока не имеют доступных URL в wiki.                                              | Сравнение Mergin Maps, QFieldCloud, HOT/OSM и MapStore/GeoServer может быть спорным при внешнем использовании.                                        | Перед публикацией перепроверить официальные URL по semantic sync/merge, roles, WFS-T, AOI/write rules, SaaS/self-hosting и pricing.                                                   |

## Связи

- [[../chats/2026-05-31-phase-f1-why-now]]
- [[../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-03-phase-f3-alternatives]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../concepts/jtbd]]
- [[../concepts/product_vision_board]]
- [[../concepts/lean_canvas]]
- [[followups/index]]
