---
title: Ф4 Решение И Scope Для Utility GIS Editor Demo
type: session
status: draft
created: 2026-06-04
updated: 2026-06-05
source: "user answers to /discover --phase Ф4, 2026-06-04; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md"
tags: [discovery, phase-f4, scope, utility-network, demo]
---

# Ф4 Решение И Scope Для Utility GIS Editor Demo

## Контекст

Ф1-Ф3 закрыли research-гипотезы до выбора primary scenario `Utility GIS editor` и baseline `ArcGIS Enterprise + Utility Network`. Ф4 фиксирует границы решения: GeoService не пытается заменить mature GIS platform, а делает demo, доказывающее, что review сетевой правки стал проще и безопаснее.

## Решения Scope

| Вопрос | Ответ Ф4 |
|---|---|
| Приоритет результата | Demo. |
| Главный пользовательский сигнал | `review стал проще`. |
| Primary demo-сценарий | `geometry/association conflict` с dirty areas, network consequence, reviewer decision и publication в authoritative state. |
| Второй сценарий | `edit after reconcile` переносится в Next/Later. |
| Обязательно входит | Conflict explanation и reviewer decision. |
| Явно не входит | Full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL, production utility network model. |
| Роли | `Editor`, `Reviewer`. |
| Модель публикации | Достаточно показать optimistic conflict + review model, а не полноценный `ArcGIS`-style branch versioning. |
| Технологические рамки | FastAPI, PostGIS, Vue/MapLibre, WebSocket, `version`/`409`. |
| Scope creep сигнал | Появление новых незапланированных на релиз фич. |

## Walking Skeleton

Минимальный end-to-end поток:

1. Пользователь входит.
2. Получает задачу.
3. Создает рабочую версию.
4. Редактирует объект сети.
5. Система сохраняет change set.
6. Валидирует сеть.
7. Сравнивает с authoritative state.
8. Показывает конфликт или отсутствие конфликта.
9. `Reviewer` подтверждает решение.
10. Изменения публикуются в `Default` / authoritative layer.
11. Пользователь видит финальное состояние как authoritative.

Skeleton должен доказать не "мы умеем рисовать объект на карте", а "мы умеем безопасно довести сетевую правку до authoritative state без silent overwrite".

## Synthetic Utility Dataset

Минимальный dataset:

| Объект | Количество |
|---|---:|
| Service area / AOI | 1 |
| Subnetwork / feeder | 1 |
| Junctions | 7 |
| Line segments | 6 |
| Devices | 6 |
| Associations | 8-10 |
| Work orders | 2 |
| Users | 3 |
| Edit versions + `Default` | 2 edit versions + `Default` |
| Conflict-сценарии | 4 заранее подготовленных сценария |

Итого: примерно 20-25 записей сетевых объектов плюс служебные записи. Это мало для быстрой реализации, но достаточно похоже на настоящую utility-сеть.

## Acceptance Criteria Source

`RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md` фиксирует детальные acceptance criteria для walking skeleton. Главный критерий: ни одна параллельная правка инженерной сети не теряется молча.

## Walking Skeleton And Dataset Source

`RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md` детализирует end-to-end поток до authoritative state, минимальные сущности/API/screens и concrete dataset `synthetic_utility_feeder_01`.

Ключевое уточнение: skeleton должен проверять жизненный цикл `draft -> validate -> reconcile -> review -> post -> authoritative`, а не только сохранение объекта на карте. Для demo достаточно change-set модели поверх `Default`, но должны быть видимы `Base`, `Mine`, `Default`, явное conflict resolution, reviewer approve и audit trail.

Минимальный dataset рекомендуется строить как electric feeder с `J-001..J-007`, `L-001..L-006`, `D-001..D-006`, `A-001..A-010`, двумя work orders и тремя пользователями: `alexey.editor`, `bolat.editor`, `marina.reviewer`.

## Открытые Места

- Нужно выбрать compact subset acceptance criteria для Release 1 demo, чтобы не превратить Ф4 scope в production branch/versioning platform.
- Нужно уточнить roadmap Now / Next / Later на основе выбранного demo-scope.

## Связи

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../entities/personas/utility_gis_editor]]
- [[../chats/2026-06-03-phase-f3-alternatives]]
- [[2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]]
