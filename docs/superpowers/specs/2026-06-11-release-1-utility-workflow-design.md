# Новый Release 1 Utility GIS Workflow

Дата: 2026-06-11
Статус: подтвержден пользователем

## Цель

Пересобрать Release 1 GeoService вокруг единственного основного сценария `Utility GIS editor`. Старый generic GIS Release 1 используется только как совместимый технический фундамент и не является самостоятельным пользовательским сценарием или критерием готовности.

## Принятое Решение

Выбран полный end-to-end vertical slice:

```text
Login
-> Work order
-> Edit version
-> Network edit
-> Validation
-> Reconcile
-> Conflict resolution
-> Submit review
-> Reviewer approval
-> Post to Default
-> Audit verification
```

Release 1 готов только тогда, когда этот путь воспроизводится локально на synthetic dataset без silent overwrite, с защитой от stale post и с доказуемым authoritative результатом.

## Продуктовая Граница

### Обязательно Входит

- роли `Editor` и `Reviewer` с separation of duties;
- назначенный `WorkOrder` и связанный AOI;
- `EditVersion`, созданная от конкретного состояния `Default`;
- изменения `NetworkFeature` и `NetworkAssociation`;
- change set без немедленной записи в authoritative state;
- demo validation rules;
- reconcile с актуальным `Default`;
- минимум один подготовленный конфликт;
- conflict diff `Base / Mine / Default`;
- явное conflict resolution;
- submit review, approve/reject и обязательный reviewer comment;
- транзакционный post в `Default`;
- сохранение edits при защитном отказе;
- полный audit trail;
- `synthetic_utility_feeder_01`;
- локальный запуск через Docker Compose.

### Не Входит

- generic GIS как самостоятельный пользовательский сценарий;
- full branch versioning;
- production topology или trace engine;
- offline mode;
- CRDT/OT;
- rich ACL;
- external GIS integrations;
- production deployment;
- реальные utility data;
- обязательное интерактивное редактирование всех GeoJSON geometry types.

## Что Переиспользуется

Текущие возможности сохраняются как внутренний foundation:

- FastAPI service/repository layering;
- JWT login;
- Postgres + PostGIS;
- MapLibre и bbox loading;
- generic Feature CRUD;
- optimistic concurrency через `version`/`409`;
- WebSocket delivery;
- Docker Compose и существующие quality gates.

Новый frontend и acceptance criteria не строятся вокруг generic layer picker или свободного Feature CRUD.

## Доменная Модель

| Сущность | Ответственность |
|---|---|
| `User`, `Role` | Пользователь и одна из взаимоисключающих ролей `Editor`/`Reviewer`. |
| `WorkOrder` | Назначенная задача, AOI, исполнитель и состояние workflow. |
| `NetworkFeature` | Junction, line или device в authoritative `Default`. |
| `NetworkAssociation` | Непространственная связь между сетевыми объектами. |
| `EditVersion` | Рабочий контекст, созданный от определенной ревизии `Default`. |
| `ChangeSet` | Feature/association changes, еще не опубликованные в `Default`. |
| `ValidationRun`, `ValidationIssue` | Запуск demo validation и найденные блокирующие/неблокирующие проблемы. |
| `ReconcileRun` | Сравнение `Base`, `Mine` и актуального `Default`. |
| `Conflict`, `ConflictResolution` | Обнаруженное несовместимое изменение и явное решение. |
| `Review` | Решение Reviewer, actor, timestamp и обязательный comment. |
| `Post` | Результат атомарной публикации change set. |
| `AuditEvent` | Append-only evidence полного workflow. |

## Жизненный Цикл

`WorkOrder`:

```text
assigned
-> editing
-> validation_failed | ready_to_reconcile
-> conflicted | ready_for_review
-> approved | rejected
-> posted
```

`EditVersion`:

```text
open
-> validated
-> reconciled
-> submitted
-> approved
-> posted | rejected
```

Инварианты:

- любое изменение после validation инвалидирует validation, reconcile и review;
- изменение после reconcile требует нового validation и reconcile;
- изменение `Default` после reconcile запрещает post и требует нового reconcile;
- approval действует только для неизмененного reconciled change set;
- защитный отказ никогда не удаляет рабочие edits;
- posted version нельзя опубликовать повторно.

Для Release 1 `EditVersion` хранится как change set поверх базовых object revisions. Полная копия utility network не требуется.

## Публичный API

```http
POST /api/v1/auth/login
GET  /api/v1/work-orders/assigned-to-me
POST /api/v1/work-orders/{workOrderId}/versions
GET  /api/v1/versions/{versionId}/workspace
PATCH /api/v1/versions/{versionId}/features/{featureId}
PUT  /api/v1/versions/{versionId}/associations/{associationId}
POST /api/v1/versions/{versionId}/validate
POST /api/v1/versions/{versionId}/reconcile
POST /api/v1/conflicts/{conflictId}/resolve
POST /api/v1/versions/{versionId}/submit-review
POST /api/v1/versions/{versionId}/approve
POST /api/v1/versions/{versionId}/reject
POST /api/v1/versions/{versionId}/post
GET  /api/v1/audit-events
```

Старые `/api/v1/layers/.../features` могут временно оставаться compatibility API и внутренним foundation. Новый основной frontend не использует их как самостоятельный workflow.

## Хранение

PostgreSQL/PostGIS хранит:

- authoritative network features и associations;
- work orders и edit versions;
- feature/association change sets;
- base revisions;
- validation runs и issues;
- reconcile runs;
- conflicts и resolutions;
- reviews;
- posts;
- append-only audit events.

### Транзакция Post

Одна database transaction:

1. Проверяет роль и separation of duties.
2. Проверяет состояние `EditVersion`.
3. Проверяет успешную validation.
4. Проверяет актуальный reconcile.
5. Проверяет отсутствие unresolved conflicts.
6. Проверяет approval.
7. Проверяет, что `Default` не изменился после reconcile.
8. Применяет change set.
9. Повышает authoritative revisions.
10. Закрывает version и work order.
11. Записывает post и audit events.
12. После commit публикует WebSocket events.

При ошибке transaction откатывается, а change set остается доступным.

## Frontend

Основные экраны:

1. `Login`
2. `My Work Orders`
3. `Edit Workspace`
4. `Validation Results`
5. `Reconcile / Conflict Review`
6. `Reviewer Queue`
7. `Post Result / Audit Trail`

`Edit Workspace` показывает work order, AOI, `EditVersion`, карту `Default`, рабочие changes, feature/association inspector и состояние workflow. `Save edit` и `Post to Default` визуально и терминологически разделены.

Conflict view показывает:

- тип конфликта;
- `Base`;
- `Mine`;
- актуальный `Default`;
- сетевое последствие;
- выбранное resolution;
- причину блокировки следующего шага.

Reviewer видит только submitted и reconciled version, diff, validation evidence и conflict resolutions. Approve/reject требует comment.

## Ошибки

Минимальные типизированные workflow errors:

- `VALIDATION_BLOCKED`;
- `UNRESOLVED_CONFLICTS`;
- `REVIEW_REQUIRED`;
- `SEPARATION_OF_DUTIES_VIOLATION`;
- `DEFAULT_CHANGED`;
- `VERSION_STATE_INVALID`;
- `POST_ALREADY_COMPLETED`.

Error body должен содержать stable code, человекочитаемое message, workflow context и рекомендуемое следующее действие.

## Demo Dataset

`synthetic_utility_feeder_01`:

- 1 AOI;
- 1 feeder;
- 7 junctions;
- 6 line segments;
- 6 devices;
- 8-10 associations;
- 2 work orders;
- 3 users;
- `Default` и 2 edit versions;
- conflict library: `Update/Update`, `Geometry/Geometry`, `Update/Delete`, `Association conflict`.

Обязательный Release 1 demo использует минимум один conflict path и один successful post.

## Acceptance Criteria

- `Editor` проходит путь от assigned work order до submit review.
- `Reviewer` отдельно approve'ит или reject'ит change set.
- validation блокирует подготовленную критическую ошибку;
- reconcile обнаруживает подготовленный conflict;
- unresolved conflict блокирует review/post;
- `Editor` не может approve собственную version;
- изменение `Default` после reconcile блокирует post;
- protective failure сохраняет edits;
- post атомарен и идемпотентен;
- authoritative state после post соответствует resolution;
- audit содержит цепочку login/work order/version/edit/validation/reconcile/conflict/review/post;
- обычный reset восстанавливает seed и сохраняет audit;
- `full-clean` удаляет demo data и audit;
- полный demo запускается локально через Docker Compose.

## Критические Тесты

- end-to-end happy path;
- validation blocker;
- prepared conflict detection;
- unresolved conflict guard;
- separation of duties;
- stale `Default` guard;
- edits survive rejected post;
- atomic and non-repeatable post;
- complete audit chain;
- reset и `full-clean`.

## Переход От Текущего Кода

1. Сохранить работающий generic foundation.
2. Добавить utility schema и seed.
3. Реализовать backend workflow/state machine.
4. Реализовать validation/reconcile/conflict resolution.
5. Реализовать reviewer и transactional post.
6. Перевести frontend на work-order workspace.
7. Добавить audit, reset/`full-clean` и demo package.
8. Провести compliance audit текущего кода против этого spec.
9. Пометить старые generic требования superseded там, где они конфликтуют.

## Принятые Гипотезы И Открытые Проверки

Принято как рабочее решение:

- `Utility GIS editor` является единственным основным сценарием Release 1;
- change-set модель используется вместо full branch versioning;
- Release 1 включает полный workflow до post;
- generic CRUD остается foundation.

Требует проверки:

- убедительность demo validation;
- понятность Save/Post и `EditVersion`/`Default`;
- достижимость P95;
- пригодность synthetic workflow как evidence;
- фактическое соответствие текущего кода новому Release 1.

## Следующие Шаги

1. Составить implementation plan и code compliance matrix.
2. Реализовать один вертикальный `WorkOrder` от login до safe post.
3. После working skeleton расширить conflict library, UX verification и benchmarks.
