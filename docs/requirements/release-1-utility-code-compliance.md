# Матрица Соответствия Кода Новому Release 1

Дата: 2026-06-11

Основание:

- `docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md`
- `Vision_wiki/decisions/release_1_utility_workflow.md`

Статусы:

- `ready` - можно переиспользовать без изменения product semantics;
- `adapt` - foundation существует, но нужен utility contract;
- `missing` - capability отсутствует;
- `superseded` - старое требование не входит в новый Release 1.

## Сводка

Текущий код является рабочим generic GIS foundation, но не реализует end-to-end `Utility GIS editor` workflow. Переиспользуются auth, PostGIS, MapLibre, bbox loading, service/repository layering, object concurrency и WebSocket infrastructure. Основная доменная модель, safety gates, review/post и audit отсутствуют.

## Матрица

| Capability                           | Статус     | Текущие Файлы                                     | Действие                                                                                           |
| ------------------------------------ | ---------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| FastAPI app и dependency wiring      | ready      | `apps/backend/app/main.py`, `api/deps.py`         | Добавлять отдельные workflow routers/services/repositories.                                        |
| SQLAlchemy/Alembic/PostGIS           | ready      | `db/session.py`, `models/`, `alembic/`            | Добавить utility schema одной новой migration chain.                                               |
| JWT login                            | adapt      | `api/auth.py`, `services/auth_service.py`         | Добавить role helpers и `reviewer`; сохранить login contract.                                      |
| Роли                                 | adapt      | `models/user.py`, `schemas/auth_user_out.py`      | Новый active workflow использует `editor`/`reviewer`; legacy `viewer` остается compatibility role. |
| Demo users                           | adapt      | `services/demo_user_seed_service.py`              | Seed `alexey.editor`, `bolat.editor`, `marina.reviewer`.                                           |
| MapLibre и bbox                      | ready      | `MapView.vue`, map composables                    | Переиспользовать карту внутри work-order workspace.                                                |
| Generic Feature CRUD                 | adapt      | `api/layers.py`, `services/feature_service.py`    | Оставить compatibility API; новый frontend пишет только в change set.                              |
| `version`/`409`                      | adapt      | `layer_repository.py`, `VersionMismatchException` | Использовать object revisions при capture base и stale checks.                                     |
| WebSocket manager                    | adapt      | `ws_layers.py`, `realtime_connection_manager.py`  | Добавить workflow/authoritative events после commit.                                               |
| `WorkOrder`                          | missing    | -                                                 | Модель, repository, service, API, frontend list.                                                   |
| `EditVersion`                        | missing    | -                                                 | Модель и state machine.                                                                            |
| `NetworkFeature` authoritative store | missing    | -                                                 | Utility-specific table, не замена legacy feature tables.                                           |
| `NetworkAssociation`                 | missing    | -                                                 | Authoritative table и change table.                                                                |
| Feature/association change set       | missing    | -                                                 | Workspace API и isolated edits.                                                                    |
| Validation                           | missing    | -                                                 | Runs, issues, demo rules, UI.                                                                      |
| Reconcile                            | missing    | -                                                 | Base/Mine/Default comparison и stale detection.                                                    |
| Domain conflicts/resolution          | missing    | -                                                 | Conflict records, explicit resolution, diff UI.                                                    |
| Reviewer queue                       | missing    | -                                                 | Submit, approve, reject, separation of duties.                                                     |
| Transactional post                   | missing    | -                                                 | Atomic apply, idempotency, stale `Default` guard.                                                  |
| Audit trail                          | missing    | -                                                 | Append-only `audit_events`, query API, UI.                                                         |
| Reset/`full-clean`                   | missing    | -                                                 | Idempotent seed reset с разной audit semantics.                                                    |
| Structured workflow errors           | missing    | `exception_handlers.py` частично                  | Stable workflow codes и next action.                                                               |
| Observability                        | adapt      | `/health`                                         | Correlation ID и structured workflow logs отсутствуют.                                             |
| Workflow frontend shell              | missing    | `App.vue` монтирует `MapPageView`                 | Role-aware `WorkflowShell`, work-order/editor/reviewer views.                                      |
| Polygon edit UX                      | adapt      | `usePolygonEditing.ts`, `stores/edit.ts`          | Переиспользовать geometry interaction для utility feature change.                                  |
| Backend unit tests                   | ready      | `apps/backend/app/tests/`                         | Продолжить service/repository style с TDD.                                                         |
| Frontend unit tests                  | ready      | Vitest tests                                      | Добавить store/contracts/component tests.                                                          |
| Full workflow acceptance             | missing    | -                                                 | Compose-based API acceptance и manual UI checklist.                                                |
| Generic all-geometry editor          | superseded | старые requirements                               | Не является Release 1 acceptance criterion.                                                        |
| Generic layer picker product flow    | superseded | `MapView.vue`                                     | Остается compatibility UI, не основной workflow.                                                   |
| Geoanalytics и `Project`             | superseded | старые requirements                               | Не входят в новый Release 1.                                                                       |

## Главные Риски Реализации

1. Смешение legacy feature mutation и utility change set может обойти review/post gates.
2. Нечеткая state invalidation может разрешить post после новых edits или изменения `Default`.
3. WebSocket event до commit может показать состояние, которого нет в `Default`.
4. Reset может уничтожить audit либо оставить невоспроизводимый seed.
5. Один большой workflow service станет трудно тестировать; ответственность нужно делить по этапам.

## Правило Миграции

- Legacy `/api/v1/layers/...` не удаляется в Release 1.
- Utility frontend не вызывает legacy mutate endpoints.
- Utility authoritative tables отделены от legacy feature tables.
- Post является единственным путем изменения utility `Default`.
- Compatibility cleanup выполняется после подтверждения нового workflow.
