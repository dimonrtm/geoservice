# Интенсив 11: Мои наряды

Дата: 2026-06-22
Статус: согласован для written spec
Расположение: `docs/release_1/sprint_1`

## Назначение

Интенсив 11 добавляет стартовый экран `Editor` после login: пользователь видит список всех назначенных ему `WorkOrders` и пустую карту с базовой подложкой.

Цель шага - дать `Editor` read-only обзор своего назначенного backlog перед началом редактирования. Экран не открывает `EditVersion`, не загружает workspace features/associations и не переводит `WorkOrder` в `in_progress`.

## Границы Scope

Входит:

- backend endpoint списка назначенных текущему `Editor` work orders;
- frontend экран `Мои наряды` рядом с пустой картой;
- локальное выделение выбранного `WorkOrder` только в списке;
- loading, empty и error states для списка;
- backend и frontend тесты для нового поведения.

Не входит:

- открытие или создание `EditVersion`;
- загрузка workspace на карту;
- отображение AOI, extent, feeder, features или associations в списке;
- подсветка выбранного `WorkOrder` на карте;
- смена статуса `WorkOrder`;
- reviewer queue, approve/reject, post и audit events.

## Backend API

Добавляется endpoint:

```http
GET /api/v1/work-orders/assigned-to-me
Authorization: Bearer <editor-token>
```

Endpoint использует текущего пользователя из Bearer token и возвращает все `WorkOrders`, где `assignee_user_id` совпадает с `current_user.id`. Фильтрации по статусу нет: в ответ входят текущие назначенные статусы `assigned` и `in_progress`.

Ответ сортируется на backend по внутреннему `updated_at DESC`, затем стабильным вторичным ключом `code ASC`. Поле `updated_at` остается внутренним storage-полем и не раскрывается в публичном контракте.

Минимальный контракт ответа:

```json
{
  "workOrders": [
    {
      "id": "uuid",
      "code": "WO-001",
      "title": "Проверка участка фидера",
      "description": "Открыть рабочий участок для последующего редактирования.",
      "status": "assigned"
    }
  ]
}
```

`AOI`, `feeder`, `EditVersion`, `features`, `associations`, `createdAt` и `updatedAt` в response не входят.

## Backend Behavior

Router остается тонким adapter'ом над существующим use-case слоем:

1. `require_editor` проверяет token и активную роль `Editor`.
2. Endpoint вызывает `WorkOrderService.list_assigned_to_editor(actor_id)`.
3. `WorkOrderService` повторно применяет существующее правило active `Editor`.
4. Repository возвращает назначенные work orders, отсортированные по `updated_at DESC`.
5. Router маппит ORM/use-case объекты в компактный response schema.

Пустой список является успешным состоянием:

```json
{
  "workOrders": []
}
```

Ошибки:

| HTTP | Code | Условие |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | token отсутствует или недействителен |
| `403` | `ROLE_NOT_ALLOWED` | пользователь не активный `Editor` |

## Frontend UX

После успешного login `Editor` видит рабочую область:

- сверху остается существующая identity/logout панель;
- слева отображается панель `Мои наряды`;
- справа отображается пустая карта с базовой подложкой;
- список загружается автоматически после восстановления/создания auth session;
- выбор строки меняет только локальный `selectedWorkOrderId`;
- выбранная строка визуально подсвечивается в списке;
- карта не меняется при выборе work order.

Список должен показывать достаточно информации для выбора:

- `code`;
- `title`;
- `status`;
- `description`, если есть.

Пустое состояние в панели списка сообщает, что назначенных work orders нет. Карта при этом остается видимой. Ошибка загрузки списка показывается в левой панели с возможностью повторить загрузку; auth/session ошибки остаются в существующем auth flow.

## Frontend Architecture

Текущий `App.vue` не должен сразу показывать `MapPageView` для `Editor`. Вместо этого он показывает новый editor shell, например `EditorWorkOrdersView`.

Предлагаемая структура:

- `apps/frontend/src/api/workOrders.ts` - `fetchAssignedWorkOrders()`;
- `apps/frontend/src/contracts/work-orders.ts` - API-типы списка;
- `apps/frontend/src/stores/workOrders.ts` или composable - loading/error/items/selected state;
- `apps/frontend/src/components/EditorWorkOrdersView.vue` - layout списка и карты;
- существующий `MapView` используется как пустая карта с подложкой.

Если текущий `MapView` автоматически загружает слой или editing state, для Интенсива 11 нужен режим/обертка, который показывает только базовую карту без workspace loading. Это изменение должно быть локальным и не должно запускать `POST /edit-versions`.

## Testing

Backend tests:

- `Editor` получает только свои назначенные work orders;
- чужие work orders не попадают в response;
- `assigned` и `in_progress` возвращаются вместе;
- response отсортирован по внутреннему `updated_at DESC`, но не содержит `updatedAt`;
- пустой список возвращает `200 { "workOrders": [] }`;
- `Reviewer` получает `403 ROLE_NOT_ALLOWED`;
- endpoint не создает `EditVersion` и не меняет статус `WorkOrder`.

Frontend tests:

- после authenticated `Editor` рендерится `Мои наряды` + карта, а не прямой editing workspace;
- список загружается через `GET /api/v1/work-orders/assigned-to-me`;
- loading, empty и error states отображаются в панели списка;
- клик по work order подсвечивает строку локально;
- клик не вызывает `POST /api/v1/work-orders/{id}/edit-versions`;
- `Reviewer` продолжает видеть свой reviewer screen.

## Развертывание И CI

Все изменения Интенсива 11 должны работать не только локально, но и в стандартном развертывании проекта и CI. Backend endpoint, frontend экран, типы, tests и build не должны требовать ручных dev-only переключателей или локальных данных вне существующего seed/startup workflow.

Обязательные gates:

- backend test suite для нового endpoint и связанных use-case/repository правил;
- frontend unit tests для списка, состояний загрузки и локального выбора;
- frontend typecheck/build;
- существующие CI jobs не должны требовать отдельной настройки для экрана `Мои наряды`;
- Docker Compose deployment должен поднимать frontend/backend так, чтобы `Editor` после login видел список назначенных `WorkOrders` и пустую карту с подложкой.

## Последствия

Интенсив 11 отделяет discovery/selection этап от editing этапа. `Editor` сначала видит назначенный backlog и карту-ориентир, а переход к `EditVersion` остается явным будущим шагом workflow.

Публичный API остается минимальным: список не раскрывает internal audit fields и не тащит данные workspace раньше времени. Сортировка по `updated_at` сохраняет удобный порядок работы без расширения response contract.
