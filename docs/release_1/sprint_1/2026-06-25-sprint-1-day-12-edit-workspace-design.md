# Интенсив 12: Edit Workspace

Дата: 2026-06-25
Статус: согласован для written spec
Расположение: `docs/release_1/sprint_1`

## Назначение

Интенсив 12 завершает frontend-переход:

```text
Login -> Мои наряды -> Create/Open EditVersion -> Edit Workspace
```

После выбора назначенного `WorkOrder` `Editor` явно открывает рабочую версию и
видит read-only workspace: `AOI`, сеть внутри рабочей области и состояние
`EditVersion`.

Цель шага - связать экран `Мои наряды` из Интенсива 11 с уже существующими
backend endpoints:

- `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
- `GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`.

Интенсив 12 не добавляет редактирование объектов, validation, reconcile,
review, post, realtime workspace-события или новый backend contract.

## Границы Scope

Входит:

- явная кнопка `Начать` для выбранного `WorkOrder` в статусе `assigned`;
- явная кнопка `Продолжить` для выбранного `WorkOrder` в статусе `in_progress`;
- открытие или повторное открытие `EditVersion` через существующий backend API;
- загрузка workspace через существующий `GET /workspace`;
- read-only карта workspace с `AOI` и network features;
- отображение состояния version: `EditVersion.status`, `baseNetworkRevision`,
  количество features, количество associations и состояние загрузки;
- локальное обновление статуса выбранного `WorkOrder` в `В работе` после
  успешного `POST /edit-versions`;
- ошибка открытия у выбранного `WorkOrder` с возможностью повторить действие;
- frontend tests для store, `EditorWorkOrdersView` и `MapView`.

Не входит:

- создание новых backend endpoints;
- изменение контракта `GET /workspace`;
- редактирование `NetworkFeature` или `NetworkAssociation`;
- toolbar старого generic layer editing;
- сохранение, удаление, optimistic feature versioning и conflict resolution;
- визуальная отрисовка associations как линий на карте;
- подсветка невыбранных work orders;
- reviewer workflow, approve/reject, post и audit events.

## UX Flow

`EditorWorkOrdersView` остается split-view:

- слева панель `Мои наряды`;
- справа карта;
- сверху остается существующая identity/logout панель.

Выбор строки в списке только делает `WorkOrder` активным. Action-кнопка
показывается только у активного `WorkOrder`, если он еще не открыт в текущем
workspace:

- `Начать` для `assigned`;
- `Продолжить` для `in_progress`.

У невыбранных `WorkOrders` кнопка не показывается.

После нажатия `Начать`:

1. frontend вызывает `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
2. backend создает `EditVersion` или возвращает существующую открытую версию;
3. после успешного `POST` выбранный `WorkOrder` локально отображается как
   `В работе`;
4. frontend вызывает `GET /workspace`;
5. после успешного `GET` справа открывается read-only workspace;
6. только после успешной загрузки workspace кнопка у выбранного `WorkOrder`
   исчезает.

После успешного нажатия `Продолжить` выполняется та же цепочка. Кнопка также
исчезает после успешной загрузки workspace.

Если `POST` или `GET /workspace` падает, ошибка показывается в левой панели у
выбранного `WorkOrder`. Кнопка остается видимой и повторяет всю цепочку. Если
`POST` уже успел перевести `WorkOrder` в `in_progress`, повторная кнопка
показывается как `Продолжить`.

## Состояние Version

В правой части workspace отображается компактная строка состояния:

- `WorkOrder.code`;
- `EditVersion.status`;
- `baseNetworkRevision`;
- `features: N`;
- `associations: N`;
- loading/error/ready состояние workspace.

Технические ids (`workOrderId`, `editVersionId`, `ownerId`) не выводятся как
основной UI. Их можно хранить в state и использовать в тестах.

## Frontend Architecture

`apps/frontend/src/api/workOrders.ts` расширяется методами:

```ts
openEditVersion(workOrderId)
fetchWorkspace(workOrderId, editVersionId)
```

`apps/frontend/src/contracts/work-orders.ts` расширяется типами:

- `OpenEditVersionResponse`;
- `EditVersionSummary`;
- `WorkspaceResponse`;
- `WorkspaceAoi`;
- `WorkspaceFeature`;
- `WorkspaceAssociation`.

Типы повторяют backend response shape:

```text
workOrder
  scope
    aoi
  editVersion
    status
    baseNetworkRevision
    features
    associations
```

Состояние Интенсива 12 можно держать в существующем
`apps/frontend/src/stores/workOrders.ts`, потому что открытый workspace прямо
связан с выбранным work order.

Минимальные новые поля:

- `openedWorkOrderId`;
- `openedEditVersionId`;
- `workspace`;
- `isOpeningWorkspace`;
- `openWorkspaceErrorByWorkOrderId`;
- `lastFittedWorkspaceKey`, где key строится из `workOrderId:editVersionId`.

Основное действие:

```text
openSelectedWorkOrder()
  -> openEditVersion(selectedWorkOrderId)
  -> mark selected work order as in_progress after successful POST
  -> fetchWorkspace(selectedWorkOrderId, editVersion.id)
  -> save opened workspace
```

Store должен защищаться от устаревших responses: если пользователь выбрал
другой `WorkOrder` во время открытия, старый response не должен перетереть
текущий selected/opened workspace.

`EditorWorkOrdersView`:

- отображает action-кнопку только у выбранного неоткрытого work order;
- вызывает `workOrders.openSelectedWorkOrder()`;
- показывает ошибку открытия у выбранной строки;
- передает workspace в `MapView`.

`MapView` получает режим:

```ts
mode: "empty" | "editing" | "workspace"
```

`mode="workspace"` не запускает legacy `loadLayers`, tile loading, layer
realtime или polygon editing.

## Map Rendering

`MapView mode="workspace"` создает MapLibre-карту и использует данные из
`WorkspaceResponse`.

Нужны read-only источники и слои:

1. `workspace:aoi`
   - GeoJSON source с `workOrder.scope.aoi.geometry`;
   - легкая заливка;
   - заметный контур.

2. `workspace:features`
   - GeoJSON source с `workOrder.editVersion.features`;
   - point features как `circle`;
   - line features как `line`;
   - polygon features как `fill` и `line` outline;
   - один source и несколько MapLibre layers с filter по geometry type.

3. `workspace:status`
   - UI-бейдж или строка поверх карты;
   - показывает состояние version и counts.

Associations в Интенсиве 12 не рисуются линиями на карте. API возвращает
associations без geometry, а вычисление anchor points или центроидов может
создать ложное ощущение точной топологии. Для этого шага associations
учитываются как часть workspace state и отображаются счетчиком.

При первом успешном открытии конкретного workspace карта делает `fitBounds` по
`AOI.extent`. Если этот же workspace уже открыт в текущем split-view и
пользователь продолжает работу, повторный render не сбрасывает viewport.

## Error Handling

`401` остается в существующем auth flow через axios interceptor: session
очищается, пользователь возвращается к login.

Ошибки `403`, `404`, `409`, `422` из open/workspace flow превращаются в
короткое пользовательское сообщение у выбранного `WorkOrder`:

```text
Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.
```

Технический `code` можно сохранить в store для тестов и debug, но основной UI
не должен становиться debug-панелью.

Если `POST` создал `EditVersion`, а `GET /workspace` упал, повторное нажатие
остается безопасным: backend idempotently вернет существующую открытую версию,
кнопка будет показана как `Продолжить`, а frontend снова попробует загрузить
workspace.

Если пользователь нажимает `Обновить` списка, открытый workspace справа
сохраняется, пока выбранный/opened `WorkOrder` остается в списке. Если он
исчезает из списка, selection и workspace очищаются.

## Testing

### Store Tests

- `openSelectedWorkOrder()` вызывает `POST /edit-versions`, затем
  `GET /workspace`.
- После успеха выбранный `assigned` локально становится `in_progress`.
- `openedWorkOrderId`, `openedEditVersionId` и `workspace` заполняются.
- Ошибка открытия сохраняется у выбранного work order.
- Ошибка открытия не заменяет готовый workspace полураскрытым состоянием.
- Устаревший response не перетирает workspace, если selection уже изменился.

### Component Tests

`EditorWorkOrdersView`:

- кнопка `Начать` видна только у выбранного `assigned`;
- кнопка `Продолжить` видна только у выбранного `in_progress`;
- после успешного открытия кнопка исчезает;
- у невыбранных work orders action-кнопок нет;
- ошибка открытия показывается у выбранного work order;
- справа используется `MapView mode="workspace"` после открытия и
  `mode="empty"` до открытия.

`MapView`:

- `mode="workspace"` не вызывает `loadLayers`, `reloadFeatures`, realtime или
  polygon editing;
- создает workspace sources/layers для AOI и features;
- показывает `EditVersion.status`, `baseNetworkRevision`, counts features и
  associations;
- вызывает `fitBounds` только при первом открытии workspace.

Backend tests в Интенсиве 12 можно не расширять, если frontend использует уже
покрытые `POST /edit-versions` и `GET /workspace` контракты. Существующие
backend API tests остаются regression gate.

## Развертывание И CI

Изменения должны работать в стандартном frontend/backend workflow без ручных
dev-only переключателей.

Обязательные gates:

- frontend unit tests для store и компонентов;
- frontend typecheck/build;
- существующие backend tests для Work Orders и Workspace API;
- стандартный Docker Compose сценарий, где seeded `Editor` после login видит
  `Мои наряды`, выбирает `WO-001`, нажимает `Начать` и получает read-only
  workspace с AOI, сетью и состоянием version.

## Последствия

Интенсив 12 превращает `Мои наряды` из read-only backlog shell в настоящий вход
в рабочий workspace, но сохраняет явную границу перед редактированием.

Старый generic `MapView mode="editing"` остается отдельно от нового
`mode="workspace"`. Это снижает риск случайно включить layer toolbar,
realtime-события или polygon editing в workflow `EditVersion`.

Associations становятся видимым состоянием workspace через count, но их
геометрическая визуализация откладывается до отдельного design, где можно
обоснованно выбрать правила anchor points и topology display.
