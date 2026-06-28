# Сброс WorkOrders при смене пользователя

Дата: 2026-06-28
Статус: согласован для written spec
Расположение: `docs/superpowers/specs`

## Назначение

Frontend хранит назначенные `WorkOrders`, выбранный `WorkOrder`, открытый workspace и ошибки открытия в Pinia store `workOrders`. Эти данные относятся к конкретному пользователю и не должны переживать смену identity в `auth` store.

Цель изменения - добавить `workOrders.reset()` и вызывать его только тогда, когда фактически изменился `auth.user.id`.

## Границы Scope

Входит:

- метод `reset()` в `apps/frontend/src/stores/workOrders.ts`;
- очистка user-scoped состояния `workOrders`;
- вызов reset из `auth` store при переходе `previousUserId !== nextUserId`;
- защита от устаревших async responses после reset;
- frontend unit tests для `workOrders` и `auth`.

Не входит:

- изменение backend API;
- изменение структуры `AuthUser`;
- изменение правил авторизации;
- очистка не связанных с пользователем frontend stores;
- новый UI для logout или восстановления сессии.

## Инвариант Identity

Единственное условие сброса:

```text
previousUserId !== nextUserId
```

`previousUserId` берется из текущего `auth.user?.id` до изменения auth state. `nextUserId` берется из нового пользователя или `null`, если пользователь очищается.

Последствия:

- `logout()` вызывает `workOrders.reset()`, если до logout был пользователь;
- повторный `logout()` без пользователя reset не вызывает;
- `loginWithPassword()` вызывает reset только если новый `user.id` отличается от предыдущего;
- `restoreSession()` вызывает reset только если `/me` вернул пользователя с другим `id`;
- временная ошибка `/me` без `401` не сбрасывает `workOrders`, потому что identity не изменилась;
- `401` остается существующим auth flow: interceptor вызывает `auth.logout()`, а reset происходит только при реальном переходе с user id на `null`.

## Frontend Design

`workOrders.reset()` возвращает store к начальному состоянию:

- `items = []`;
- `isLoading = false`;
- `errorMessage = null`;
- `selectedWorkOrderId = null`;
- `openedWorkOrderId = null`;
- `openedEditVersionId = null`;
- `workspace = null`;
- `isOpeningWorkspace = false`;
- `openWorkspaceErrorByWorkOrderId = {}`;
- `lastFittedWorkspaceKey = null`;
- async request sequence increments, чтобы pending responses не восстановили старые данные.

Для аккуратности лучше вынести фабрику начального состояния, чтобы `state()` и `reset()` использовали один источник дефолтов.

`auth` store получает небольшой внутренний helper, который:

1. запоминает `previousUserId`;
2. применяет изменение `token`/`user`/session fields/localStorage;
3. сравнивает `previousUserId` и `nextUserId`;
4. вызывает `useWorkOrdersStore().reset()` только при отличии id.

Так coupling остается локальным: `auth` уже является источником identity, а `workOrders` остается владельцем собственной очистки.

## Async Safety

В `workOrders` уже есть `openWorkspaceRequestSeq` для защиты `openSelectedWorkOrder()`. `reset()` должен увеличивать sequence, чтобы открытие workspace, начатое до logout или смены пользователя, не смогло записать старый workspace после сброса.

`loadAssigned()` тоже должен быть защищен sequence-проверкой или общим request id. Иначе запрос списка, начатый до смены пользователя, может завершиться позже и записать старые `items` после reset.

## Error Handling

Reset не показывает отдельную ошибку пользователю. Это silent cleanup user-scoped state.

Существующее поведение auth сохраняется:

- при `401` вызывается `logout()`;
- при временной ошибке `/me` без `401` token остается, `sessionError` заполняется, `workOrders` не сбрасывается без смены id;
- localStorage очищается или обновляется существующими auth actions.

## Testing

`apps/frontend/src/stores/workOrders.test.ts`:

- `reset()` очищает список, selection, workspace, errors, loading flags и fitted key;
- `reset()` инвалидирует pending `openSelectedWorkOrder()` response;
- pending `loadAssigned()` response после reset не записывает старые `items`.

`apps/frontend/src/stores/auth.test.ts`:

- `logout()` с текущим `user.id` вызывает `workOrders.reset()`;
- повторный `logout()` без пользователя не вызывает reset;
- `setAuth()` или login с тем же `user.id` не вызывает reset;
- `setAuth()` или login с другим `user.id` вызывает reset;
- `restoreSession()` с тем же `user.id` не вызывает reset;
- `restoreSession()` с другим `user.id` вызывает reset;
- временная ошибка `/me` без `401` не вызывает reset.

Regression gate:

```powershell
npm run test -- --run src/stores/workOrders.test.ts src/stores/auth.test.ts
npm run typecheck
```

## Последствия

После изменения frontend не будет показывать старые назначенные work orders или workspace после смены пользователя. Поведение остается точным: reset привязан к смене identity, а не к техническим событиям вроде успешного `restoreSession()`.
