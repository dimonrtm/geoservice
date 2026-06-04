---
title: Release 1 MVP
type: concept
status: active
created: 2026-05-30
updated: 2026-06-04
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md"
tags: [concept, release-1, mvp, collaboration]
---

# Release 1 MVP

## Определение

Release 1 MVP - вертикальный срез GeoService, где пользователь проходит путь от login до просмотра GeoJSON-слоя на MapLibre-карте и совместного редактирования Feature с конфликтами через `version`/`409`.

После Ф4 основной demonstrable result уточнен как demo для `Utility GIS editor`: working version, change set, validation, compare with authoritative state, conflict explanation, reviewer decision и publication без silent overwrite.

## Что Известно

- Команда и ограничение источника: 1 разработчик, 2 недели, обучение встроено в задачи.
- Основной результат: два клиента видят один слой, один меняет Feature, второй получает WebSocket-обновление в течение 1-2 секунд или `409 Conflict` при сохранении устаревшей версии.
- Минимальные роли: `Viewer` для чтения и `Editor` для чтения, создания, редактирования и удаления.
- Минимальные сущности: `Layer`, `Feature`, `ImportResult`; `Project` упоминается как будущая или отложенная область.
- Минимальная готовность: JWT login, 2D карта, загрузка слоев через bbox, редактирование объектов, WebSocket realtime, `409 Conflict`, CI/CD и документация запуска.

## Неясно

- Должен ли Release 1 включать GeoJSON import как обязательный P1 scope или как демонстрационный bonus после P0.

## Ф4 Scope Boundary

В текущий demo-scope входят conflict explanation и reviewer decision. GeoService показывает собственную optimistic conflict + review model; full branch versioning, topology engine, offline sync, CRDT/OT, rich ACL и production utility network model явно не входят в текущую фазу.

Главный критерий готовности: ни одна параллельная правка инженерной сети не теряется молча.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md`
- `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`

## Связи

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
- [[../chats/2026-05-31-initial-discover]]
