# Спринт 1, День 10: Workspace API И AOI В Контексте WorkOrder

Дата: 2026-06-21
Статус: согласован для design spec
Расположение: `docs/release_1/sprint_1`

## Назначение

День 10 реализует backend-only workspace API для активной `EditVersion`.

Цель дня:

```text
GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace
-> возвращает назначенному Editor read-only workspace активной EditVersion
```

Workspace должен вернуть агрегат `WorkOrder` с его рабочей областью `AOI`,
активную `EditVersion`, рабочие `features` и `associations` этой версии.
Справочный `feeder` не входит в обязательный response Дня 10.

Frontend, изменение сети, validation, reconcile, review и post не входят в этот
день.

## Принятое Решение По AOI

`AOI` относится к контексту `WorkOrder`, а не к контексту пользователя и не к
`utility_network`.

Основание:

- пользователь получает `WorkOrder` и открывает связанный рабочий участок;
- один пользователь может работать с разными AOI в разных задачах;
- один AOI может быть связан с разными задачами и редакторами;
- AOI отвечает на вопрос "где выполняется конкретный наряд";
- пользовательские `allowedAreas` в будущем могут быть policy/ACL guard, но не
  владельцем workspace AOI.

Поэтому `AOI` переносится в bounded context/schema `work_order`.

## Границы Контекстов

Финальная граница для этой задачи:

```text
work_order
  aois
  work_orders
  edit_versions
  edit_version_features
  edit_version_associations

utility_network
  feeders
  network_features
  network_associations
  network_states
```

Между bounded contexts не должно быть FK. Связь между `work_order` и
`utility_network` выполняется только через repositories/application layer.

Разрешенные FK внутри `work_order`:

```text
work_order.work_orders.aoi_id -> work_order.aois.id
work_order.edit_versions.work_order_id -> work_order.work_orders.id
work_order.edit_version_features.edit_version_id -> work_order.edit_versions.id
work_order.edit_version_associations.edit_version_id -> work_order.edit_versions.id
```

Не разрешены:

```text
work_order.* -> utility_network.*
utility_network.* -> work_order.*
user.* -> work_order.*
work_order.* -> user.*
```

## Storage И Migration Direction

Добавить таблицу `work_order.aois`:

| Поле | Правило |
|---|---|
| `id` | UUID primary key |
| `name` | обязательное имя рабочей области |
| `description` | nullable |
| `geometry` | `Polygon` или `MultiPolygon`, `SRID 4326` |
| `created_at` | timestamp |
| `updated_at` | timestamp |

Geometry constraints повторяют текущие требования к AOI:

- geometry не пустая;
- `ST_IsValid(geometry)`;
- `ST_SRID(geometry) = 4326`;
- `GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')`;
- spatial index на `geometry`.

Добавить в `work_order.work_orders`:

```text
aoi_id UUID NOT NULL
```

`aoi_id` имеет FK только на `work_order.aois.id`.

`utility_network.aois` больше не является владельцем AOI. Utility dataset seed
больше не должен создавать AOI; AOI создается или обеспечивается в work order
seed/scope.

## Агрегат WorkOrder

Доменная форма для workspace:

```text
WorkOrder
  scope
    aoi
  editVersion
    features
    associations
```

`EditVersion`, ее рабочие `features` и `associations` остаются частью агрегата
`WorkOrder`. Эта задача меняет принадлежность AOI, но не перестраивает всю
модель данных вокруг отдельного `networkContext`.

`Feeder` остается в `utility_network`. Если feeder metadata понадобится для
следующего API/UI шага, `WorkspaceService` должен получать его через существующий
`UtilityNetworkRepository`, а не через новый repository или FK.
`Feeder` не является источником workspace `features` или `associations`.

## API Contract

Endpoint:

```http
GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace
Authorization: Bearer <editor-token>
```

Precondition:

```text
Workspace API вызывается только после успешного
POST /api/v1/work-orders/{workOrderId}/edit-versions.
```

Endpoint не создает `EditVersion`, не открывает `WorkOrder` и не выполняет
auto-open. Если `WorkOrder` еще не имеет активной `EditVersion`, клиент должен
сначала вызвать create/open endpoint. `workOrderId` и `editVersionId` должны
указывать на один aggregate `WorkOrder`; mismatch, чужой `WorkOrder`, чужая
`EditVersion` или отсутствующая `EditVersion` возвращают
`404 EDIT_VERSION_NOT_FOUND`.

Response shape:

```json
{
  "workOrder": {
    "id": "c80fd056-d80f-4bf4-8694-89fc1936ab99",
    "code": "WO-001",
    "title": "Проверка участка фидера",
    "description": "Открыть рабочий участок для последующего редактирования.",
    "status": "in_progress",
    "scope": {
      "aoi": {
        "id": "19e7cc20-9171-468a-a69c-914662c17f02",
        "name": "Рабочая область WO-001",
        "description": null,
        "geometry": {
          "type": "Polygon",
          "coordinates": []
        },
        "extent": [65.5, 44.8, 65.54, 44.84]
      }
    },
    "editVersion": {
      "id": "a57ec6e1-7eaa-473e-a335-4d02a5e7678e",
      "status": "open",
      "baseNetworkRevision": 1,
      "features": {
        "type": "FeatureCollection",
        "features": []
      },
      "associations": []
    }
  }
}
```

Feeder metadata в response Дня 10 не включается. Если позже понадобится
справочный `references.feeder`, использовать существующий `UtilityNetworkRepository`;
новый repository для feeder не создается.

## WorkspaceService Behavior

`WorkspaceService` выполняет use-case правила:

1. Проверить Bearer token и активную роль `Editor`.
2. Найти `WorkOrder` по `workOrderId` и `EditVersion` внутри этого агрегата.
3. Проверить, что `WorkOrder.assignee_user_id` совпадает с текущим actor.
4. Проверить, что `WorkOrder.status = in_progress`.
5. Проверить, что `EditVersion.status = open`.
6. Загрузить `WorkOrder.scope.aoi` из `work_order.aois`.
7. Вернуть рабочие `EditVersionFeature`, geometry которых пересекает AOI.
8. Вернуть только те `EditVersionAssociation`, у которых оба конца есть в
   отфильтрованном наборе features.
9. Не читать feeder aggregate для получения workspace features/associations.

Workspace network data читается из `work_order.edit_version_features` и
`work_order.edit_version_associations`, а не из authoritative
`utility_network.network_features` и `utility_network.network_associations`.

Пересекающая geometry возвращается целиком, без clipping по AOI.

## Ошибки

| HTTP | `code` | Условие |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | Токен отсутствует или недействителен |
| `403` | `ROLE_NOT_ALLOWED` | Пользователь не активный `Editor` |
| `404` | `EDIT_VERSION_NOT_FOUND` | WorkOrder/EditVersion отсутствуют, чужие или не связаны друг с другом |
| `409` | `EDIT_VERSION_STATE_CONFLICT` | WorkOrder/EditVersion в неподходящем состоянии |
| `422` | `WORKSPACE_CONTEXT_INVALID` | Отсутствует AOI, поврежден scope или associations неконсистентны |

Чужая и отсутствующая `EditVersion` возвращают одинаковый `404`, чтобы не
раскрывать существование чужих задач.

## Test Scope

### Metadata / Model Tests

- `AOI` живет в schema `work_order`, не в `utility_network`.
- `WorkOrder.aoi_id` обязателен.
- FK `work_order.work_orders.aoi_id -> work_order.aois.id` существует.
- Cross-context FK между `work_order` и `utility_network` отсутствуют.

### Migration Tests

- `work_order.aois` создается с geometry constraints и spatial index.
- `utility_network.aois` больше не является владельцем AOI.
- Upgrade/downgrade создают ожидаемую структуру для dev/CI окружений.

### Seed Tests

- `seed_work_orders` создает или обеспечивает AOI scope для `WO-001`.
- Повторный seed не дублирует AOI и не перезаписывает существующий WorkOrder.
- `seed_utility_dataset` больше не отвечает за AOI.

### Workspace Service / API Tests

- Назначенный активный `Editor` получает workspace.
- `Reviewer` получает `403`.
- Чужая, отсутствующая или не принадлежащая указанному `WorkOrder` `EditVersion`
  возвращает `404 EDIT_VERSION_NOT_FOUND`.
- Endpoint не создает `EditVersion` и не меняет `WorkOrder.status`.
- Response содержит `workOrder.scope.aoi`.
- Features берутся из `edit_version_features` и фильтруются по AOI intersection.
- Associations возвращаются только если оба конца есть в filtered features.
- Поврежденный context возвращает `422 WORKSPACE_CONTEXT_INVALID`.

### Focused Integration

После clean seed и открытия edit version endpoint возвращает `WO-001`, AOI scope,
рабочие features и associations demo workspace. Для текущего demo AOI ожидается
полный рабочий slice `synthetic_utility_feeder_01`: 19 features и 9 associations,
если все объекты пересекают AOI.

## Не Входит В Scope

- Frontend workspace screen.
- Editing API для features/associations.
- Validation, reconcile, conflict resolution, review или post.
- Перестройка `EditVersion` как отдельного bounded context.
- Новый feeder repository.
- FK между `work_order` и `utility_network`.
- User-level `allowedAreas` / rich ACL.

## Consequences

- AOI становится устойчивой частью scope наряда.
- Workspace API больше не должен угадывать AOI через spatial intersection,
  `DefaultState` или seed-допущения.
- `WorkOrder` остается корнем workflow aggregate.
- `EditVersion` и рабочие копии features/associations остаются внутри
  `WorkOrder` aggregate.
- `utility_network` остается владельцем сетевого authoritative/reference
  контекста, включая feeder.
