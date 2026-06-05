---
title: Architecture Vision
type: solution
status: active
created: 2026-05-30
updated: 2026-06-05
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md"
tags: [solution, architecture, release-1]
---

# Architecture Vision

Высокоуровневое видение Release 1 MVP по `RAW_inputs/documents/спринт 1.odt`. Детальные текущие факты реализации остаются в `Code_wiki/архитектура/`.

## Системы И Границы

| Система | Ответственность | Граница |
|---|---|---|
| Frontend Vue + MapLibre | Login state, layer discovery, bbox loading, edit UI, conflict notification, WebSocket subscription | Не хранит source-of-truth; применяет API/WS contracts и перезагружает данные после reconnect/conflict. |
| Backend FastAPI | REST API, auth, role checks, feature validation, optimistic concurrency, WebSocket broadcast | HTTP/WebSocket boundary под `/api/v1`; бизнес-правила в services, SQL в repositories. |
| Postgres + PostGIS | Хранение geometry/properties/version, spatial filtering, GiST indexes | SRID 4326; bbox через `ST_MakeEnvelope`/`ST_Intersects`. |
| CI/dev environment | Воспроизводимость разработки и demo | Docker Compose, lint/tests/build/smoke commands, README/run docs. |

## Потоки Данных

| Поток | Источник | Получатель | Примечания |
|---|---|---|---|
| Layers discovery | Frontend | `GET /api/v1/layers` | Возвращает UUID layers и geometry metadata; frontend не hardcode'ит table endpoints. |
| Map bbox loading | Map viewport | Backend/PostGIS | `GET /api/v1/layers/{layerId}/features?bbox=...&limit=...`, FeatureCollection response. |
| Feature edit | Editor UI | Backend service/repository | `PATCH` с `version`; success increments version, mismatch returns `409`. |
| Delete | Editor UI | Backend service/repository | `DELETE` требует `version`; mismatch не удаляет объект. |
| Realtime broadcast | Backend after create/update/delete | WebSocket subscribers | События слоя доставляются другим клиентам за 1-2 секунды. |
| GeoJSON import | Editor upload | Backend/PostGIS | SYNC import `FeatureCollection <=20MB`, summary response, данные видны через bbox. |

## Ключевые Компромиссы

| Решение | Альтернатива | Почему |
|---|---|---|
| Optimistic concurrency через `version` и `409` | CRDT/OT или locks | Дешевле и достаточно для 2-недельного MVP; silent overwrite запрещен. |
| WebSocket pub/sub по layer | Полный collaborative state engine | Release 1 нужен broadcast изменений, не сложный merge. |
| Bbox loading вместо тайлов/cache/offline | Tile pipeline или offline cache | Быстрее получить end-to-end map loading и ограничить объем данных через `limit`. |
| Две роли `Viewer`/`Editor` | Rich ACL на уровне объектов/полей | Простая модель прав закрывает Release 1 demo. |
| SYNC GeoJSON import <=20MB | Async import pipeline и большие форматы | Достаточно для demo data; большие форматы отложены. |

## Ф4 Architecture Boundary

Ф4 сохраняет технологические рамки: FastAPI, PostGIS, Vue/MapLibre, WebSocket и `version`/`409`. Для demo вводятся роли `Editor` и `Reviewer`.

| Capability | Ф4 Подход | Не Делать В Текущей Фазе |
|---|---|---|
| Working version | Модель рабочей версии / edit version поверх `Default` для demo-flow | Full branch versioning platform |
| Conflict handling | Optimistic conflict + review model, explicit reviewer decision, no silent overwrite | CRDT/OT, locks как основной механизм |
| Validation | Demo validation достаточная для synthetic utility dataset | Production topology engine |
| Publication | Controlled publish в `Default` / authoritative layer после validation, compare и review | Production utility network source of truth |
| UX | Conflict explanation и reviewer decision screen | Rich enterprise workflow/ACL |

Главный архитектурный тест: сетевая правка проходит от working version до authoritative state без silent overwrite и с понятным review decision.

## Ф4 Desired Technical Skeleton

Источник `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md` фиксирует desired technical shape для demo, а не текущее состояние реализации.

### Минимальная Предметная Модель

| Сущность | Назначение |
|---|---|
| `User`, `Role` | login/RBAC и separation of duties между editor/reviewer. |
| `WorkOrder` | контекст назначенной сетевой правки. |
| `NetworkVersion` | isolated edit version от `Default`. |
| `NetworkFeature`, `NetworkAssociation` | объекты сети и связи между ними. |
| `ChangeSet` | old/new values без немедленной записи в authoritative state. |
| `ValidationIssue` | результат demo topology validation. |
| `Conflict`, `ConflictResolution` | reconcile outcome и явное решение конфликта. |
| `AuthoritativeSnapshot` | состояние `Default`, с которым сравнивается рабочая версия. |
| `AuditLog` | доказательство цепочки edit -> review -> post. |

### Desired API Surface

```http
POST /auth/login
GET  /work-orders/assigned-to-me
POST /work-orders/{workOrderId}/versions
GET  /versions/{versionId}/features
PATCH /versions/{versionId}/features/{featureId}
POST /versions/{versionId}/associations
POST /versions/{versionId}/validate
POST /versions/{versionId}/reconcile
POST /conflicts/{conflictId}/resolve
POST /versions/{versionId}/submit-review
POST /versions/{versionId}/approve
POST /versions/{versionId}/post
GET  /authoritative/features/{featureId}
```

### Storage И Frontend

Working version можно хранить как change-set (`base_version_id`, `feature_id`, `operation`, `old_value`, `new_value`, `changed_by`, `changed_at`), а не как полную копию сети.

Минимальные backend tables: `users`, `roles`, `work_orders`, `network_features_default`, `network_associations_default`, `network_versions`, `network_feature_changes`, `network_association_changes`, `validation_issues`, `reconcile_runs`, `conflicts`, `conflict_resolutions`, `audit_log`.

Минимальные frontend screens: `Login`, `My work orders`, `Map editor`, `Reconcile/conflict view`, `Review/post result`.

Минимальные validation rules: device не orphan, line имеет `from_junction`/`to_junction`, transformer соединяет `10kV` и `0.4kV`, normally-open tie switch не создает активную петлю без разрешения, post запрещен при unresolved validation issues.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md`
- `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
