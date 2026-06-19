# Спринт 1, День 8: EditVersion От Default

Дата: 2026-06-19
Статус: согласован пользователем для design spec
Расположение: `docs/release_1/sprint_1`

## Назначение

День 8 реализует backend foundation для создания и повторного открытия `EditVersion` от текущего состояния `Default`.

Цель дня - добавить минимальную, но настоящую доменную основу для участка workflow:

```text
Login -> My Work Orders -> Create/Open EditVersion
```

День 8 не создает workspace API и не добавляет редактирование сети. `EditVersion` в этом design является изолированным рабочим контейнером и фиксирует revision boundary, но не материализует snapshot признаков сети.

## Выбранный Подход

Используется явная backend-модель `DefaultState` и `EditVersion`.

`DefaultState` представляет опубликованное authoritative-состояние `Default`:

```text
DefaultState(name="default", current_revision=1)
```

`EditVersion` создается от текущей ревизии `Default`:

```text
EditVersion(
  work_order_id,
  owner_id,
  base_revision,
  status="open",
  created_at,
  last_opened_at
)
```

`base_revision` копируется из `DefaultState.current_revision` при создании `EditVersion` и больше не меняется.

## Смысл Base Revision

`EditVersion` не получает собственные копии `NetworkFeature` и `NetworkAssociation`.

Сетевые признаки остаются в authoritative Default-таблицах:

- `utility_network.network_features`;
- `utility_network.network_associations`.

Будущий `GET /workspace` будет собирать read-only slice так:

```text
EditVersion
  -> WorkOrder
      -> AOI
      -> Feeder
          -> NetworkFeature из Default
          -> NetworkAssociation из Default
```

`base_revision` отвечает на вопрос: от какой опубликованной ревизии `Default` редактор начал работу. В Sprint 1 `Default` считается стабильным read-only baseline. Историческое чтение `Default` по старым ревизиям, snapshot сети и change log не входят в День 8.

Если в будущих спринтах `Default` начнет меняться параллельно с открытыми `EditVersion`, потребуется отдельный механизм revisioned storage, snapshot или change log. День 8 только фиксирует boundary для будущих `reconcile` и `post`.

## Модель Данных

Добавляются две таблицы в schema `utility_network`.

### `default_states`

Минимальные поля:

- `id` - UUID primary key;
- `name` - string, unique, для Sprint 1 используется значение `default`;
- `current_revision` - integer, `>= 1`;
- `created_at`;
- `updated_at`.

В Sprint 1 поддерживается ровно один доменный `DefaultState` с `name="default"`. Отсутствие этой строки при открытии `EditVersion` считается поврежденным контекстом.

### `edit_versions`

Минимальные поля:

- `id` - UUID primary key;
- `work_order_id` - FK на `utility_network.work_orders.id`;
- `owner_id` - FK на `users.id`;
- `base_revision` - integer, `>= 1`;
- `status` - enum/check, в Sprint 1 только `open`;
- `created_at`;
- `last_opened_at`.

Storage-инвариант: у одного `WorkOrder` не может быть больше одной active `EditVersion`. Это защищается partial unique index:

```text
unique(work_order_id) where status = 'open'
```

Сервисная проверка не заменяет этот index, потому что конкурентные `POST`-запросы должны быть защищены на уровне storage constraint.

## Поведение Открытия

Endpoint:

```text
POST /api/v1/work-orders/{workOrderId}/edit-versions
```

Request body отсутствует.

State machine Дня 8:

```text
WorkOrder.assigned
  + нет open EditVersion
  -> создать EditVersion
  -> WorkOrder.in_progress
  -> HTTP 201 created=true

WorkOrder.in_progress
  + есть open EditVersion
  -> вернуть существующую EditVersion
  -> обновить last_opened_at
  -> HTTP 200 created=false

WorkOrder.assigned
  + есть open EditVersion
  -> HTTP 422 WORK_ORDER_CONTEXT_INVALID

WorkOrder.in_progress
  + нет open EditVersion
  -> HTTP 422 WORK_ORDER_CONTEXT_INVALID
```

Backend не выполняет auto-healing рассинхрона между `WorkOrder.status` и active `EditVersion`. Такой рассинхрон должен быть видимым дефектом транзакции, seed, миграции или ручного вмешательства.

## API Response

Success response при создании, HTTP `201`:

```json
{
  "created": true,
  "editVersion": {
    "id": "a57ec6e1-7eaa-473e-a335-4d02a5e7678e",
    "workOrderId": "c80fd056-d80f-4bf4-8694-89fc1936ab99",
    "ownerId": "7ca660f0-3606-497b-b52d-9ac11f06178c",
    "status": "open",
    "baseRevision": 1,
    "createdAt": "2026-06-19T09:00:00Z",
    "lastOpenedAt": "2026-06-19T09:00:00Z"
  }
}
```

Success response при повторном открытии, HTTP `200`, имеет ту же форму, но `created=false`. `lastOpenedAt` может быть обновлен.

Ошибки:

| HTTP | `code` | Значение |
|---|---|---|
| `401` | `AUTH_REQUIRED` | Требуется вход в систему. |
| `403` | `ROLE_NOT_ALLOWED` | Роль пользователя не допускает операцию. |
| `404` | `WORK_ORDER_NOT_FOUND` | Рабочая задача не найдена или не видима текущему пользователю. |
| `409` | `WORK_ORDER_STATE_CONFLICT` | Состояние задачи не допускает операцию. |
| `422` | `WORK_ORDER_CONTEXT_INVALID` | Контекст задачи или Default поврежден либо неполон. |

Для чужого `WorkOrder` публичный API возвращает `404 WORK_ORDER_NOT_FOUND`, чтобы не раскрывать существование чужих задач.

## Кодовые Границы

Backend infrastructure:

- `models/utility_network/default_state.py`;
- `models/utility_network/edit_version.py`;
- обновление `models/utility_network/__init__.py`;
- Alembic migration для `default_states`, `edit_versions`, FK, CHECK constraints и partial unique index;
- `repositories/default_state_repository.py`;
- `repositories/edit_version_repository.py`.

Use cases:

- новый `EditVersionService`;
- service result `created + edit_version`;
- зависимости сервиса только от `AsyncSession` и repositories.

`EditVersionService` не зависит от `WorkOrderService` или других сервисов. Сервисы в этом кодовом участке зависят только от репозиториев.

Если правила доступа должны быть общими между `WorkOrderService` и `EditVersionService`, они выносятся только в чистые guard-функции без доступа к БД и без зависимости от сервисов. Допустимые guards принимают уже загруженные объекты и проверяют роль, активность, assignment или status.

Web API:

- новый router для work order workflow, например `work_orders.py`;
- endpoint `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
- response schemas `EditVersionOut` и `OpenEditVersionOut`;
- подключение router в `main.py`;
- ошибки мапятся в существующую форму `ErrorResponse`.

## Тестовый Scope

Обязательное покрытие:

- metadata test для `DefaultState` и `EditVersion`;
- проверка FK, CHECK constraints и partial unique index;
- unit tests `EditVersionService`;
- API tests для `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
- integration test, подтверждающий, что storage не допускает две open `EditVersion` для одного `WorkOrder`.

Ключевые сценарии unit tests:

- `assigned` WorkOrder создает `EditVersion` от `DefaultState.current_revision`;
- создание переводит `WorkOrder` в `in_progress`;
- `in_progress` с active `EditVersion` возвращает существующую version и `created=false`;
- `Reviewer`, inactive user и пользователь без назначения не открывают version;
- missing `DefaultState(name="default")` возвращает `WORK_ORDER_CONTEXT_INVALID`;
- `assigned` с existing open version возвращает `WORK_ORDER_CONTEXT_INVALID`;
- `in_progress` без existing open version возвращает `WORK_ORDER_CONTEXT_INVALID`.

## Не Входит В День 8

- `GET /api/v1/edit-versions/{editVersionId}/workspace`;
- frontend `My Work Orders` и `Edit Workspace`;
- snapshot сети;
- change set;
- редактирование `NetworkFeature` или `NetworkAssociation`;
- validation, reconcile и post;
- reviewer workflow;
- историческое чтение `Default` по старым ревизиям.

## Критерии Готовности

День 8 считается готовым, когда:

1. В БД есть `DefaultState` и `EditVersion` с нужными constraints.
2. Startup/migration path гарантирует наличие `DefaultState(name="default", current_revision=1)`.
3. `POST /api/v1/work-orders/{workOrderId}/edit-versions` создает version для assigned `WorkOrder`.
4. Повторный `POST` возвращает существующую open version.
5. `WorkOrder` атомарно переходит `assigned -> in_progress` при первом создании version.
6. Конкурентное создание не может породить две open version для одного `WorkOrder`.
7. Сервисный слой не зависит от других сервисов, только от repositories.
8. Workspace, frontend и change set остаются вне scope.

## Последствия Решения

День 8 создает устойчивую основу для будущего workspace API: у frontend появится id рабочей версии, а backend сможет отличать первое создание от повторного открытия.

Решение сознательно не решает историческое чтение Default. Это допустимо для Sprint 1, потому что Default остается read-only baseline. Когда появятся `reconcile` и `post`, потребуется отдельный design для хранения изменений и повышения `Default.current_revision`.
