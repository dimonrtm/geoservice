---
title: User Story Map
type: solution
status: active
created: 2026-05-30
updated: 2026-05-31
source: RAW_inputs/documents/спринт 1.odt
tags: [solution, usm, release-1]
---

# User Story Map

User Story Map для Release 1 MVP по источнику `RAW_inputs/documents/спринт 1.odt`.

## Backbone

| Активность | Пользовательская Цель | Примечания |
|---|---|---|
| Авторизоваться | Получить доступ к защищенным endpoints | Bearer token обязателен для всех запросов; роли `Viewer` и `Editor`. |
| Найти слой | Получить список доступных layers | `GET /api/v1/layers`, UUID id, `geometryType`, `srid=4326`; frontend не hardcode'ит table endpoints. |
| Смотреть данные на карте | Видеть Feature из выбранного слоя в текущем viewport | MapLibre загружает GeoJSON FeatureCollection через bbox endpoint при pan/zoom. |
| Редактировать Feature | Менять geometry/properties без silent overwrite чужих изменений | `PATCH` с обязательным `version`; при mismatch сервер возвращает `409`. |
| Удалять Feature | Удалять объект только при актуальной версии | `DELETE` также проверяет `version`; при mismatch возвращает `409`. |
| Импортировать demo data | Быстро добавить небольшой GeoJSON для демо | SYNC import до 20MB, только `FeatureCollection`, geometry type должен совпадать со слоем. |

## Walking Skeleton

| Шаг | Минимальное Поведение | Статус |
|---|---|---|
| Login | `Viewer`/`Editor` получает token, endpoints без token возвращают `401` | required |
| Layers discovery | `GET /api/v1/layers` возвращает минимум points/polygons/lines | required |
| Bbox loading | Карта запрашивает `GET /api/v1/layers/{layerId}/features?bbox=...&limit=...` и рисует FeatureCollection | required |
| Single-user edit | `Editor` создает/меняет/удаляет Feature, получает обновленную Feature с `version` | required |
| Two-tabs conflict | Клиент A сохраняет `V -> V+1`, клиент B с `V` получает `409 VERSION_MISMATCH` | required |
| Realtime update | Другие клиенты получают create/update/delete через WebSocket за 1-2 секунды | required |
| GeoJSON import | `Editor` загружает `FeatureCollection <=20MB`, получает summary и видит данные через bbox | candidate |

## Releases

| Release | Scope | Критерий Готовности |
|---|---|---|
| Release 1 P0 | Layers discovery, bbox map loading, optimistic edit conflict, minimal CI/docs | Demo script two tabs воспроизводится; API возвращает `401/403/404/409/422` по контракту. |
| Release 1 P1 | SYNC GeoJSON import, upload UI, import summary | После import данные видны через bbox; ошибки import ограничены и валидируются. |
| Later | Projects/Layers persistence, CRDT/OT, offline, locks, rich ACL, topology validation, large imports | Возвращаться после подтверждения Release 1 MVP и новых требований. |

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- [[../concepts/first_release_mvp]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
