---
title: User Story Map
type: solution
status: active
created: 2026-05-30
updated: 2026-06-05
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md"
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

## Discovery Ф2: Provisional JTBD

Этот раздел не расширяет scope Release 1. Он фиксирует primary research-scenario `Utility GIS editor` и deferred кадастровый сценарий перед Ф4.

| Persona-Кандидат | Job | Статус |
|---|---|---|
| `Utility GIS editor` | Изолировать изменения инженерной сети, увидеть конфликт с authoritative state и контролируемо опубликовать результат после review | primary hypothesis |
| Кадастровый инженер | Сохранить lineage участков, разобрать конфликт и опубликовать согласованное кадастровое изменение | deferred hypothesis |

## Discovery Ф4: Demo Scope

Ф4 фиксирует текущий scope как demo, а не production replacement для `ArcGIS Enterprise + Utility Network`. Главный пользовательский сигнал: `review стал проще`.

### MVP / Demo

| Элемент | Статус | Примечания |
|---|---|---|
| `geometry/association conflict` | required | Primary demo-сценарий с dirty areas, network consequence, reviewer decision и publication в authoritative state. |
| Conflict explanation | required | Пользователь и reviewer должны понимать base value, edit version value, current `Default` и сетевое последствие. |
| Reviewer decision | required | `Reviewer` принимает approve/reject/resolution decision перед publication. |
| Optimistic conflict + review model | required | Достаточно собственной модели, не требуется full branch versioning. |
| `edit after reconcile` | Next/Later | Сильный второй сценарий, но не MVP текущей Ф4. |

### Ф4 Walking Skeleton

| Шаг | Минимальное Поведение | Статус |
|---|---|---|
| Login | `Editor` или `Reviewer` входит в систему | required |
| Work order | `Editor` получает назначенную задачу | required |
| Working version | Для задачи создается рабочая версия от `Default` | required |
| Network edit | `Editor` меняет объект сети и/или association | required |
| Change set | Система сохраняет old/new values без изменения authoritative state | required |
| Validation | Система валидирует сетевую правку в рамках demo-правил | required |
| Compare | Система сравнивает working version с authoritative state | required |
| Conflict explanation | Система показывает конфликт или отсутствие конфликта | required |
| Review | `Reviewer` подтверждает решение | required |
| Publish | Изменения публикуются в `Default` / authoritative layer | required |
| Final state | Пользователь видит итоговое authoritative state | required |
| Audit trail | Цепочка login/work order/version/edit/validation/reconcile/review/post видна в audit log | required |

Skeleton должен доказать не "мы умеем рисовать объект на карте", а "мы умеем безопасно довести сетевую правку до authoritative state без silent overwrite".

Минимальный успешный тест из уточняющего RAW source:

1. `Editor A` входит, открывает `WO-001` и создает `V-WO-001-ALEXEY`.
2. `Editor A` меняет `D-002 Switch` и association.
3. `Editor B` меняет тот же объект или связанную `L-003` и публикует в `Default`.
4. `Editor A` запускает reconcile.
5. Система показывает конфликт через `Base`, `Mine`, `Default`.
6. Конфликт явно разрешается.
7. `Reviewer` смотрит diff, approve'ит и post'ит результат в `Default`.
8. Read-only пользователь видит authoritative state, а audit log показывает всю цепочку.

### Synthetic Utility Dataset

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
| Conflict-сценарии | 4 |

Оценка размера: 20-25 записей сетевых объектов плюс служебные записи.

Рекомендуемый конкретный dataset: `synthetic_utility_feeder_01` - маленький electric feeder с `J-001..J-007`, `L-001..L-006`, `D-001..D-006`, `A-001..A-010`, `WO-001`, `WO-002`, `alexey.editor`, `bolat.editor`, `marina.reviewer`, `Default`, `V-WO-001-ALEXEY`, `V-WO-002-BOLAT`.

Conflict library для demo: `Update/Update`, `Geometry/Geometry`, `Update/Delete`, `Association conflict`.

### Явно Не Входит

- Full branch versioning.
- Topology engine.
- Offline sync.
- CRDT/OT.
- Rich ACL.
- Production utility network model.

### Acceptance Criteria

Детальные критерии находятся в `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`. Главный критерий: ни одна параллельная правка инженерной сети не теряется молча.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `RAW_inputs/documents/Ф2.md`
- [[../concepts/first_release_mvp]]
- [[../concepts/jtbd]]
- [[../entities/personas/utility_gis_editor]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../chats/2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
