---
title: Risk And Assumption Log
type: risk
status: active
created: 2026-05-31
updated: 2026-06-06
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; RAW_inputs/documents/Ф2.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md; RAW_inputs/documents/03.06.2026deep-research-report.md; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md; Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md; RAW_inputs/documents/utility_gis_editor_target_times.md"
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
| AS-2026-06-05-001 | accepted-for-demo | Минимальный non-toy dataset для demo - `synthetic_utility_feeder_01`: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions и 4 conflict-сценария. | Реализовать dataset так, чтобы он проверял topology, associations, invalid state, parallel editing, conflict detection, review, post и audit trail. |
| AS-2026-06-05-002 | accepted-for-demo | Первый rollout GeoService - local Docker Compose demo для разработчика и владельца pet-проекта; ценность - `learning value` и доказательство, что pipeline стал проще. | Проверить через README/demo script: developer запускает локально `Editor flow` на synthetic dataset без external GIS. |
| AS-2026-06-06-001 | accepted-for-demo | Для первого demo достаточно Chrome и reference hardware Asus TUF Gaming 2022, AMD Ryzen 7 5000 series, 16 GB RAM; startup/reset могут занимать несколько минут. | Запустить end-to-end demo на reference hardware и записать фактические времена startup, reset и ключевых операций. |
| AS-2026-06-06-002 | hypothesis | P95 targets из `utility_gis_editor_target_times.md` достижимы на малом `synthetic_utility_feeder_01`: map <=5 сек, save <=2/5 сек, validation <=15 сек, reconcile <=10/20 сек, diff <=5 сек, post <=15 сек. | Выполнить repeatable benchmark в Chrome на reference hardware и сравнить P50/P95 с draft thresholds. |

## Риски

| ID                | Статус    | Риск                                                                                                                            | Влияние                                                                                                                                               | Снижение Риска                                                                                                                                                                        |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RK-2026-05-31-001 | mitigated | Цель первого релиза была сформулирована как "все типа работает"; Ф4 заменила ее на demo walking skeleton и acceptance criteria. | Риск снова появится, если критерии из `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` не будут сжаты в реализуемый Release 1 subset. | Держать главный критерий: ни одна параллельная правка инженерной сети не теряется молча.                                                                                              |
| RK-2026-05-31-002 | mitigated | Проект может остаться незавершенным репозиторием на GitHub.                                                                     | Исследовательская и portfolio-ценность не материализуются.                                                                                            | Ф4 выбрала минимальный demonstrable результат: demo, где `review стал проще`.                                                                                                         |
| RK-2026-06-01-001 | open      | Research перечисляет много полезных capabilities, а выбранный utility-сценарий сам по себе сложнее Release 1.                   | Scope GeoService может преждевременно разрастись до branch mode, reviewer workflow и topology validation.                                             | Ф4 non-goals: full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL, production utility network model. Scope creep сигнал - новые незапланированные на релиз фичи. |
| RK-2026-06-03-001 | mitigated | `ArcGIS Enterprise + Utility Network` уже является good-enough incumbent для полноценного authoritative utility editing.        | GeoService как продукт может быть не нужен, если не покажет сильное преимущество в explainability или review productivity.                            | Ф4 зафиксировала demo focused conflict/review layer, а не попытку заменить mature GIS platform.                                                                                       |
| RK-2026-06-03-002 | open      | Non-Esri vendor-specific claims из Ф3 research пока не имеют доступных URL в wiki.                                              | Сравнение Mergin Maps, QFieldCloud, HOT/OSM и MapStore/GeoServer может быть спорным при внешнем использовании.                                        | Перед публикацией перепроверить официальные URL по semantic sync/merge, roles, WFS-T, AOI/write rules, SaaS/self-hosting и pricing.                                                   |
| RK-2026-06-05-001 | open      | Детализированный walking skeleton легко принять за требование full branch/versioning platform.                                  | Реализация может уйти в production-grade topology/versioning вместо focused demo.                                                                     | Считать source желаемой demo-траекторией: change-set поверх `Default`, demo validation, четыре synthetic conflict-сценария и explicit non-goals Ф4 остаются границей.                 |
| RK-2026-06-05-002 | open      | Непонятный UI conflict review может сломать первое developer demo.                                                              | Даже при рабочем backend pipeline пользователь не увидит, что review стал проще.                                                                      | В Now/Next держать focus на `Editor flow`, clear conflict review states, demo script checkpoints и troubleshooting.                                                                   |
| RK-2026-06-06-001 | open      | Неявная семантика reset может либо уничтожить audit evidence, либо оставить demo в невоспроизводимом состоянии.                 | Повторный demo нельзя надежно воспроизвести или проверить историю действий.                                                                           | Разделить обычный reset, который восстанавливает seed и сохраняет audit, и `full-clean`, который удаляет demo data и audit.                                                           |
| RK-2026-06-06-002 | open      | Draft performance targets могут оказаться недостижимыми или нестабильными на reference hardware.                                | Acceptance criteria будут формально определены, но demo не пройдет их воспроизводимо.                                                                 | Добавить benchmark harness/сценарий, фиксировать P50/P95 и пересматривать target только по измерениям, не по единичному запуску.                                                      |

## Связи

- [[../chats/2026-05-31-phase-f1-why-now]]
- [[../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-03-phase-f3-alternatives]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../chats/2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]]
- [[../chats/2026-06-05-phase-f5-business-rollout]]
- [[../chats/2026-06-06-phase-f6-constraints-and-nfr]]
- [[../chats/2026-06-06-utility-gis-editor-target-times]]
- [[../concepts/jtbd]]
- [[../concepts/product_vision_board]]
- [[../concepts/lean_canvas]]
- [[followups/index]]
