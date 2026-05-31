---
title: Release 1 MVP
type: concept
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [concept, release-1, mvp, collaboration]
---

# Release 1 MVP

## Определение

Release 1 MVP - вертикальный срез GeoService, где пользователь проходит путь от login до просмотра GeoJSON-слоя на MapLibre-карте и совместного редактирования Feature с конфликтами через `version`/`409`.

## Что Известно

- Команда и ограничение источника: 1 разработчик, 2 недели, обучение встроено в задачи.
- Основной результат: два клиента видят один слой, один меняет Feature, второй получает WebSocket-обновление в течение 1-2 секунд или `409 Conflict` при сохранении устаревшей версии.
- Минимальные роли: `Viewer` для чтения и `Editor` для чтения, создания, редактирования и удаления.
- Минимальные сущности: `Layer`, `Feature`, `ImportResult`; `Project` упоминается как будущая или отложенная область.
- Минимальная готовность: JWT login, 2D карта, загрузка слоев через bbox, редактирование объектов, WebSocket realtime, `409 Conflict`, CI/CD и документация запуска.

## Неясно

- Должен ли Release 1 включать GeoJSON import как обязательный P1 scope или как демонстрационный bonus после P0.

## Источники

- `RAW_inputs/documents/спринт 1.odt`

## Связи

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
- [[../chats/2026-05-31-initial-discover]]
