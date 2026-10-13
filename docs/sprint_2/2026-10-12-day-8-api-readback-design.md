# День 8 — API сохранения и durable readback

Дата: 2026-10-12. Календарная задача: понедельник, 10 августа 2026 года.

Статус: цельная спецификация принята пользователем 2026-10-12 («Принимаю»). После сверки источников сохранена parsing boundary Дня 4. [План реализации](2026-10-12-day-8-api-readback-plan.md) подготовлен отдельно для проверки и выбора способа исполнения. Реализация не начата.

## 1. Цель и границы

Дать UI публичное сохранение геометрии и чтение актуального persisted draft, достаточное для следующего Save и Revert без локального знания seed coordinates. Используются существующие Save service, command registry, history, immutable baseline и workspace GET.

Входит:

- geometry PUT поверх существующего parser и Save service;
- строгие ошибки PUT и workspace GET;
- token, persisted change set, validation и baseline в workspace;
- API/OpenAPI, workspace service/repository и HTTP + DB проверки.

При подготовке плана обнаружено необходимое условие browser-доступности: `web_api/main.py` пока не включает PUT в CORS allow_methods. Подключение нового метода включает разрешение PUT и preflight regression test без расширения списка допустимых origins. Это техническое обеспечение уже согласованного API для UI.

Не входят: TypeScript contracts/API client Дня 9, UI recovery подзадачи S2-X01, новый формат fingerprint, новая таблица, изменение Save transaction protocol, отдельная команда Revert, polling, исправление данных при GET или расширение редактирования на другие geometry types. Existing open response не расширяется; исходный token доступен через workspace.

Продуктовый код, configuration, migrations и тесты в рамках подготовки этой спецификации не изменяются. Git add/commit/push запрещены правилами репозитория.

## 2. Основания

- [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md), разделы 9–11, AC-03–AC-09.
- [Календарный план](2026-07-31-sprint-2-calendar-plan.md), Дни 8–9 и этап restart/recovery.
- [Спецификация Дня 4](2026-10-08-day-4-geometry-design.md), раздел 4: точный parser и ошибки до use case.
- [Спецификация Дня 6](2026-10-11-day-6-save-design.md) и [Дня 7](2026-10-11-day-7-rejections-events-revert-design.md): Save, replay, terminal rejection, guards, events и Revert.
- [Решение о восстановлении Save](2026-10-12-save-recovery-rules-decision.md): результат команды отделён от актуального readback.
- `Wiki/value_objects/command_id.md`, `Wiki/specifications/edit_version_has_persisted_change_set.md`, `Wiki/specifications/edit_version_basic_draft_validation.md`.
- `DDD_Wiki/aggregates/edit_version.md`, `DDD_Wiki/state_machines/edit_version_save_request.md`, `DDD_Wiki/state_machines/editor_save_recovery.md`.
- [Анализ и уточнения](2026-10-12-day-8-api-readback-analysis.md).

В некоторых старых Wiki/DDD_Wiki фрагментах ещё упоминаются pending response и current object/token внутри stale error. Для этого среза действуют более поздние принятые решения: synchronous terminal result, строгая ошибка из трёх полей и отдельное чтение актуальных данных. Исправление старых страниц не выполняется этой задачей автоматически.

## 3. Публичный Save

```http
PUT /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/features/{feature_id}/geometry
```

Path IDs — UUID. Body содержит ровно `commandId`, `draftVersionToken`, `geometry`. Actor определяется авторизацией.

### 3.1. Существующий parsing contract

Используется `apps/backend/utility_service/web_api/parsers/geometry_save_request.py`, функция `parse_geometry_save_request`. JSON bytes передаются в parser до преобразования координат через float. Повторная реализация parsing в Pydantic не подменяет его правила.

Допустимая форма:

- commandId — UUID-строка;
- draftVersionToken — непустая строка без trim, Unicode normalization и числового преобразования;
- geometry содержит только `type="LineString"` и `coordinates`;
- coordinates — минимум две XY-пары конечных JSON numbers;
- X в `[-180,180]`, Y в `[-90,90]`;
- числовой token координаты не длиннее 64 символов, модуль явной exponent не больше 324;
- неизвестные и повторяющиеся JSON keys запрещены.

Другой geometry type, пустая/одноточечная линия, Z/M, неправильная вложенность, строковые/boolean/null координаты, NaN/Infinity и нарушение ограничений — request format errors. Они возвращают `422 REQUEST_VALIDATION_ERROR`, не вызывают Save и не резервируют CommandId. Исправленный запрос может использовать тот же ID, если он не занят ранее выполненной командой.

Двухвершинная LineString проходит parser. Несоответствие количества вершин eligible baseline проверяется уже доменом и даёт сохраняемый `GEOMETRY_STRUCTURE_CHANGED`.

### 3.2. Выполнение

Route передаёт результат parser в существующий `EditVersionService.save_geometry`. Service остаётся владельцем единственной transaction. Его порядок guards, identity/replay, reservation, mutation, events и terminal result не перестраивается.

Успех возвращается после commit. Ожидаемый domain rejection возвращается после сохранения terminal rejection согласно Дню 7. Infrastructure failure откатывает transaction; router не превращает его в успешный ответ или сохраняемый domain rejection.

HTTP 200 содержит прежний payload:

- commandId и commandState=`succeeded`;
- draftVersionToken;
- operation=`updated|unchanged`;
- hasPersistedChangeSet;
- updatedFeature с id и geometry;
- basicValidation либо null.

При непустом diff basicValidation содержит geometryStatus=`passed`, aoiStatus=`passed`, positionalAccuracyStatus=`POSITIONAL_ACCURACY_UNVERIFIED`, dirtyRelativeToBaseline=`passed`. При baseline/no-op baseline/Revert summary равен null, как в принятом контракте Дня 6.

### 3.3. Retry и Revert

Matching retry возвращает сохранённый результат при выполнении текущих access/lifecycle guards. Существующие `geom-v1` и `geom-contextless-v1` не меняются. Разные сырые координаты могут иметь одинаковую идентичность по действующим canonicalization rules; отличие JSON formatting само по себе не означает COMMAND_ID_REUSED.

Replay подтверждает исходную команду и может содержать исторические geometry/token. Актуальное состояние берётся из workspace. Обычный committed rejection не выполняется заново после исправления контекста; access retry сохраняет отдельное правило Дня 7.

Revert — новый PUT с baseline geometry, текущим token и новым CommandId. Новый endpoint или флаг revert не вводится.

## 4. Ошибки и права

Новый PUT и существующий workspace GET используют ровно:

```json
{"code":"...","message":"...","correlationId":"..."}
```

CorrelationId относится к текущему HTTP-запросу и соответствует принятому middleware/header contract. Он не хранится в terminal rejection и не добавляется в успешный payload. Ошибки не содержат detail/details, current geometry или token.

| HTTP | Код/область |
| --- | --- |
| 401 | AUTH_REQUIRED |
| 403 | USER_INACTIVE, ROLE_NOT_ALLOWED |
| 404 | EDIT_VERSION_NOT_FOUND |
| 409 | DRAFT_VERSION_STALE, COMMAND_ID_REUSED, MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED, SAVE_CONTEXT_CLOSED; для GET — EDIT_VERSION_STATE_CONFLICT |
| 422 | REQUEST_VALIDATION_ERROR; существующие FEATURE_NOT_EDITABLE, WORK_ORDER_CONTEXT_INVALID, GEOMETRY_STRUCTURE_CHANGED, GEOMETRY_INVALID, GEOMETRY_OUTSIDE_AOI; для GET — WORKSPACE_CONTEXT_INVALID |
| 500 | INTERNAL_ERROR по существующему handler |

Require_editor и текущая auth dependency остаются. Авторизационный отказ до use case не занимает CommandId. Assignment проверяется сервисом; чужой target маскируется как EDIT_VERSION_NOT_FOUND. Owner не заменяет assignee. При отсутствии адресуемого target запись registry не создаётся. Приоритет доменных отказов и исключения подготовки identity сохраняются по Дням 6–7.

GeometryRequestFormatError и FastAPI request validation errors для этих операций отображаются в REQUEST_VALIDATION_ERROR. Решение локализуется по двум endpoint-контрактам, а не меняет глобально ответы legacy API или list/open. Для JSON/path validation нельзя случайно вернуть стандартный FastAPI detail.

## 5. Workspace readback

```http
GET /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace
```

Прежние поля, вложенность `workOrder.editVersion`, AOI-фильтр отображаемых features и правило присутствия обоих концов association сохраняются.

В `workOrder.editVersion` добавляются обязательные поля:

| Поле | Значение |
| --- | --- |
| draftVersionToken | Строковое представление текущей draft_revision; клиент трактует как opaque token |
| hasPersistedChangeSet | Boolean, текущий diff всей версии |
| basicValidation | Сокращённый summary сохранённого draft либо null |
| changeSet | Объект единственного изменения либо null |

Непустой changeSet содержит `featureId`, `vertexIndex` (с нуля в baseline), `baselineGeometry` (полная LineString), `operation="updated"`. Current geometry остаётся в features. Baseline связан именно через `EditVersion.default_state_id`; другой активный Default не подставляется.

| Состояние | hasPersistedChangeSet | basicValidation | changeSet |
| --- | --- | --- | --- |
| До изменения | false | null | null |
| Сохранённый допустимый diff | true | Summary | Объект |
| После Revert | false | null | null |

После Revert token отражает выполненное изменение и не сбрасывается на 1. GET, no-op и replay сами по себе не меняют revision. Старый replay не заменяет текущую геометрию readback.

### 5.1. Данные и согласованность

Расширяется существующая цепочка `workspace_aggregate.sql` → repository row → `WorkOrderRepository.get_workspace_aggregate` → `WorkspaceService` → response schemas.

Один SQL statement читает revision, current/baseline данные, assignment, lifecycle и существующий workspace. Числовое сравнение и сборка projection выполняются над этим снимком без дополнительных читающих SELECT. GET не берёт Save root lock и не использует transaction-bound mutation handles.

Проверка persisted diff относится ко всей версии до AOI-фильтра отображения. Нельзя считать отсутствие видимой updated feature доказательством отсутствия change set. Согласованность проверяется по фактическим baseline/current данным, а не только флагу operation. При проверке unchanged объектов не вводится требование редактируемости: исходные points и двухвершинные линии могут штатно оставаться неизменёнными.

Допустимое изменение — одна eligible existing line, ровно одна внутренняя вершина относительно baseline. VertexIndex вычисляется из фактического diff. Нет дополнительной canonicalization при GET. Current/baseline сериализуются через существующий обратимый EWKB codec; особенно важен точный off-grid baseline для Revert.

### 5.2. Validation и повреждённый контекст

Summary описывает текущий сохранённый draft и гарантии прошедшего Save, а не новую проверку качества при GET. Он воспроизводится из согласованной persisted projection; произвольный старый command payload не используется как источник текущего состояния. Нет новой проверки позиционной точности/топологии или внешнего контекста.

Отсутствие нужного baseline, несовместимая связь исходного состояния, несогласованность operation/diff, несколько изменённых объектов, недопустимая структура diff или скрытое AOI-фильтром изменение дают `422 WORKSPACE_CONTEXT_INVALID`. Не возвращается нормальный пустой changeSet и не выполняется repair. Ошибки декодирования контекста должны доходить до этого mapping, даже если возникают в repository mapping до service projection.

Workspace сохраняет guards: активный Editor; чужая/отсутствующая версия — 404; lifecycle не in_progress/open — 409 EDIT_VERSION_STATE_CONFLICT. Частичный успешный workspace с недостоверными данными Revert не вводится.

## 6. OpenAPI

Request schema описывает строгий LineString XY с минимум двумя вершинами, обязательные поля, UUID, непустой token и запрет extras. Ограничения исходной числовой записи, duplicate keys и точного Decimal parsing объясняются текстом, поскольку одной стандартной JSON Schema недостаточно.

Успешный PUT, расширенный workspace и error body имеют явные схемы. Nullable поля обязательны и возвращаются как null, а не исчезают. Для обеих операций 422 документирует строгую error schema вместо стандартного HTTPValidationError. Другие фактические auth/domain/internal responses перечислены по применимости.

Schema успешного Save не должна пересобирать replay с потерей полей или дополнительным округлением чисел. OpenAPI review сверяет generated document с реальными HTTP responses, а не только наличие моделей в исходниках.

## 7. Матрица проверки для итогового review

| ID | Проверка | Ожидаемое доказательство |
| --- | --- | --- |
| D8-01 | Успешный PUT через HTTP | Правильные actor/IDs/request; 200 и canonical payload после commit |
| D8-02 | Короткая линия, другой type, Z/M, JSON/UUID errors, extras, duplicate keys, числовые ограничения | 422 REQUEST_VALIDATION_ERROR; Save не вызван, новая registry row не появилась |
| D8-03 | Принятый parser request с нарушением доменного правила | Существующий код и durable rejection; mutation/revision/history не меняются |
| D8-04 | Auth, Editor, assignment, lifecycle | Текущие guards и маскировка; строгая error shape PUT/GET |
| D8-05 | Повтор success/rejection, другой payload под тем же ID | Существующий replay/COMMAND_ID_REUSED; текущий correlationId |
| D8-06 | Начальный GET, Save → GET, no-op → GET, Revert → GET | Поля, nullability, актуальный token, точный baseline и vertexIndex |
| D8-07 | Старый success replay после более нового Save | Исторический ответ команды и свежий workspace различаются ожидаемо; данные не откатываются |
| D8-08 | Недостающий baseline, неверные operation/diff, несколько изменений, скрытое AOI изменение | WORKSPACE_CONTEXT_INVALID; нет ложного чистого workspace |
| D8-09 | GET одновременно с Save | Целиком старый либо новый snapshot; нет смешения token/geometry/baseline |
| D8-10 | HTTP + реальная БД, новый клиент/session/service instance | Save → независимый readback → Revert; durable terminal rejection; неизменный DefaultState |
| D8-11 | Midpoint, отрицательный midpoint, off-grid baseline, equivalent JSON numbers | Сохранение точности parser/codec и прежней fingerprint semantics |
| D8-12 | Generated OpenAPI, CORS preflight и регрессия других routes | Схемы соответствуют HTTP; PUT разрешён для настроенного origin; list/open/legacy contract не изменён |

API tests с service doubles проверяют routing/serialization, но не заменяют HTTP + DB сценарии. Репозиторные проверки подтверждают один SQL snapshot. Тесты Дней 4/6/7 переиспользуются как регрессия без создания параллельной реализации Save.

Новая session/service instance не считается фактическим restart процесса. Полный browser/backend restart smoke остаётся обязательным результатом спринта на календарном этапе restart/recovery; отдельной заявленной проверкой Дня 8 он не подменяется. Сейчас тесты реализации не запускались.

## 8. Затрагиваемые области и результат

Backend paths относительно `apps/backend/utility_service/`:

- `web_api/api/work_orders.py`, локальное подключение error mapping и OpenAPI models, `web_api/main.py` для разрешения PUT в CORS;
- существующий `web_api/parsers/geometry_save_request.py` как переиспользуемая граница;
- `use_cases/schemas/edit_version/`, `use_cases/schemas/workspace/`;
- `infrastructure/postgresql/sql/workspace_aggregate.sql`, `repository_rows/workspace.py`, `repositories/work_order_repository.py`;
- `use_cases/services/workspace_service.py` и соответствующие API/service/repository/integration tests.

Save service, geometry core и fingerprint protocols сохраняют принятые правила; изменение их поведения не является задачей подключения endpoint. Новые таблицы, migration и baseline backfill не требуются.

День 8 завершён после прохождения согласованной матрицы и OpenAPI review, когда UI может получить Save result и полный актуальный readback через публичный API. Это не объявляет завершёнными frontend Дня 9, S2-X01 или весь Sprint 2.
