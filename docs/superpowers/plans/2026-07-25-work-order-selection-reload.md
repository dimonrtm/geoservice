# WorkOrder Selection Reload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сохранять последний выбранный WorkOrder в `sessionStorage`, восстанавливать его preview-панель после reload текущей вкладки и очищать клиентский workspace при переходе к другому WorkOrder.

**Architecture:** `workOrders` store остаётся единственным владельцем selection и workspace state. Новый маркер `geoservice:selected-work-order` дополняет существующий `geoservice:opened-workspace`; восстановление сначала определяет актуальный выбор по назначенному списку, а workspace загружает только при совпадении обоих маркеров. `auth` store сохраняет оба маркера только во время первоначальной гидратации той же сессии и очищает их при logout или смене пользователя.

**Tech Stack:** Vue 3.5, Pinia 3, TypeScript 5.9, Vitest 3, Vue Test Utils, jsdom `sessionStorage`.

## Global Constraints

- Persistence действует только в текущей вкладке через `sessionStorage`; `localStorage` и URL не используются.
- `geoservice:selected-work-order` хранит JSON `{workOrderId}` без WorkOrder business data.
- При выборе другого WorkOrder старый workspace удаляется только из frontend state; серверная `EditVersion` не закрывается и не удаляется.
- Workspace после reload загружается через `GET` только когда selected и opened markers относятся к одному WorkOrder.
- Различающиеся markers сохраняют последний выбор, удаляют opened marker и не запускают скрытый workspace `GET`.
- Старая вкладка только с `geoservice:opened-workspace` должна восстановить выбор и workspace.
- Backend, API-контракты, `WorkspaceDetailsPanel` и multi-workspace caching не изменяются.
- Новые пользовательские тексты и документация пишутся на русском; identifiers, paths, API names и types не переводятся.
- Следовать TDD: для каждого поведения сначала получить ожидаемый failing test, затем внести минимальное изменение и повторно запустить тест.
- По правилам `AGENTS.md` агент не выполняет `git add`, `git commit` или `git push`; каждый task заканчивается review checkpoint, а staging и commit выполняет пользователь.

---

## File Structure

- Modify: `apps/frontend/src/stores/workOrders.ts`
  - владеет чтением, записью и валидацией selected/opened markers;
  - очищает workspace при смене selection;
  - согласует persisted state с актуальным `assigned-to-me` списком.
- Modify: `apps/frontend/src/stores/workOrders.test.ts`
  - unit tests storage lifecycle, switching, reload reconciliation, backward compatibility и races.
- Modify: `apps/frontend/src/stores/auth.ts`
  - передаёт store два независимых preserve flags только для initial session restore.
- Modify: `apps/frontend/src/stores/auth.test.ts`
  - проверяет initial preservation и очистку markers при user lifecycle changes.
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
  - component regression tests восстановленной preview-панели и отсутствия скрытого workspace cache.
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`
  - использует один `loadAssignedAndRestore()` flow для mount, refresh и retry.
- Reference: `docs/superpowers/specs/2026-07-25-work-order-selection-reload-design.md`
  - одобренный источник требований.

Новые runtime-файлы и зависимости не нужны.

---

### Task 1: Persist Selection And Evict The Previous Client Workspace

**Files:**

- Modify: `apps/frontend/src/stores/workOrders.test.ts:120-260`
- Modify: `apps/frontend/src/stores/workOrders.ts:49-130`
- Modify: `apps/frontend/src/stores/workOrders.ts:204-262`

**Interfaces:**

- Consumes: существующие `sessionStorageOrNull()`,
  `clearStoredOpenedWorkspace()` и `clearOpenedWorkspace()`.
- Produces:
  - `SELECTED_WORK_ORDER_STORAGE_KEY =
    "geoservice:selected-work-order"`;
  - `storeSelectedWorkOrder(workOrderId: string): void`;
  - `clearStoredSelectedWorkOrder(): void`;
  - `ResetWorkOrdersOptions.preserveSelectedWorkOrder?: boolean`;
  - `selectWorkOrder(workOrderId: string): void`, который не очищает
    workspace при повторном выборе того же id и очищает его при смене id.

- [ ] **Step 1: Add failing tests for selection persistence and workspace eviction**

В `workOrders.test.ts` рядом с существующими storage tests добавить константы:

```ts
const SELECTED_WORK_ORDER_STORAGE_KEY =
  "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";
```

Добавить тест записи selection:

```ts
it("persists the selected work order in session storage", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();

  store.selectWorkOrder("wo-1");

  expect(store.selectedWorkOrderId).toBe("wo-1");
  expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
    JSON.stringify({ workOrderId: "wo-1" }),
  );
});
```

Добавить тест повторного выбора:

```ts
it("keeps the opened workspace when the same work order is selected again", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.selectWorkOrder("wo-1");
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = workspaceResponse("wo-1", "ev-1");
  sessionStorage.setItem(
    OPENED_WORKSPACE_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );

  store.selectWorkOrder("wo-1");

  expect(store.workspace?.workOrder.id).toBe("wo-1");
  expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBe(
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );
});
```

Добавить тест смены WorkOrder:

```ts
it("evicts the client workspace when another work order is selected", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.selectWorkOrder("wo-1");
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = workspaceResponse("wo-1", "ev-1");
  sessionStorage.setItem(
    OPENED_WORKSPACE_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );

  store.selectWorkOrder("wo-2");

  expect(store.selectedWorkOrderId).toBe("wo-2");
  expect(store.openedWorkOrderId).toBeNull();
  expect(store.openedEditVersionId).toBeNull();
  expect(store.workspace).toBeNull();
  expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
  expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
    JSON.stringify({ workOrderId: "wo-2" }),
  );
});
```

- [ ] **Step 2: Run the focused tests and verify the intended failures**

Run from `apps/frontend`:

```powershell
npm test -- src/stores/workOrders.test.ts
```

Expected before implementation:

- selection marker assertion fails because the key is absent;
- different selection leaves `openedWorkOrderId`, `workspace` and opened marker
  intact.

- [ ] **Step 3: Add selected marker helpers and reset policy**

В `workOrders.ts` рядом с `StoredOpenedWorkspace` обновить reset options и
добавить storage key:

```ts
export type ResetWorkOrdersOptions = {
  preserveOpenedWorkspace?: boolean;
  preserveSelectedWorkOrder?: boolean;
};

const SELECTED_WORK_ORDER_STORAGE_KEY =
  "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";
```

Заменить существующее определение `ResetWorkOrdersOptions`, не оставляя
дубликат type alias.

Добавить безопасные helpers рядом с opened-workspace helpers:

```ts
function clearStoredSelectedWorkOrder(): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(SELECTED_WORK_ORDER_STORAGE_KEY);
  } catch {
    // Nothing to clean up if browser storage is unavailable.
  }
}

function storeSelectedWorkOrder(workOrderId: string): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId }),
    );
  } catch {
    // The in-memory selection remains valid if browser storage is unavailable.
  }
}
```

Обновить `reset()` так, чтобы flags управляли markers независимо:

```ts
if (!options.preserveSelectedWorkOrder) {
  clearStoredSelectedWorkOrder();
}
if (!options.preserveOpenedWorkspace) {
  clearStoredOpenedWorkspace();
}
```

- [ ] **Step 4: Implement selection transitions**

Заменить `selectWorkOrder()` и дополнить `clearSelection()`:

```ts
selectWorkOrder(workOrderId: string): void {
  if (this.selectedWorkOrderId === workOrderId) {
    storeSelectedWorkOrder(workOrderId);
    return;
  }

  this.clearOpenedWorkspace();
  this.selectedWorkOrderId = workOrderId;
  storeSelectedWorkOrder(workOrderId);
},
clearSelection(): void {
  this.selectedWorkOrderId = null;
  clearStoredSelectedWorkOrder();
  this.clearOpenedWorkspace();
},
```

`clearOpenedWorkspace()` должен остаться selection-neutral: он очищает только
opened ids, workspace, fit key и opened marker.

- [ ] **Step 5: Extend reset and storage-failure tests**

В существующем reset test записать оба markers и проверить, что обычный
`reset()` удаляет оба.

Существующий preserve test переименовать в
`"can reset in-memory state while preserving work order session markers"` и
вызвать:

```ts
store.reset({
  preserveOpenedWorkspace: true,
  preserveSelectedWorkOrder: true,
});
```

Проверить, что оба значения `sessionStorage` сохранились, а Pinia state
очистился.

Добавить тест недоступной записи:

```ts
it("keeps selection in memory when session storage writes fail", async () => {
  const setItemSpy = vi
    .spyOn(Storage.prototype, "setItem")
    .mockImplementation(() => {
      throw new DOMException("storage unavailable", "SecurityError");
    });

  try {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    expect(() => store.selectWorkOrder("wo-1")).not.toThrow();
    expect(store.selectedWorkOrderId).toBe("wo-1");
  } finally {
    setItemSpy.mockRestore();
  }
});
```

- [ ] **Step 6: Run Task 1 tests**

Run:

```powershell
npm test -- src/stores/workOrders.test.ts
npm run typecheck
```

Expected: both commands exit `0`; all existing opening/race tests remain green.

- [ ] **Step 7: Review checkpoint**

Inspect:

```powershell
git diff --check -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts
git diff -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts
```

Expected: no whitespace errors; diff contains only selected marker lifecycle
and switch-eviction behavior. Leave all changes unstaged for user review.

---

### Task 2: Reconcile Selected And Opened Markers On Reload

**Files:**

- Modify: `apps/frontend/src/stores/workOrders.test.ts:394-580`
- Modify: `apps/frontend/src/stores/workOrders.ts:218-450`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue:29-60`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue:96-110`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts:79-140`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts:543-620`

**Interfaces:**

- Consumes:
  - `storeSelectedWorkOrder(workOrderId: string): void`;
  - `clearStoredSelectedWorkOrder(): void`;
  - existing `readStoredOpenedWorkspace()` and `fetchWorkspace()`.
- Produces:
  - `StoredSelectedWorkOrder = { workOrderId: string }`;
  - `readStoredSelectedWorkOrder(): StoredSelectedWorkOrder | null`;
  - расширенный `restoreOpenedWorkspace(): Promise<void>`, который сначала
    восстанавливает selection, а workspace загружает только для совпадающих
    markers;
  - backward-compatible fallback from opened marker to selection;
  - `loadAssignedAndRestore(): Promise<void>` для mount, refresh и retry;
  - component behavior: persisted selection renders preview after mount.

- [ ] **Step 1: Add failing store tests for selection-only restore and mismatched markers**

Добавить selection-only test:

```ts
it("restores a selected work order without fetching a workspace", async () => {
  sessionStorage.setItem(
    SELECTED_WORK_ORDER_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1" }),
  );

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: null,
      status: "assigned",
    },
  ];

  await store.restoreOpenedWorkspace();

  expect(store.selectedWorkOrderId).toBe("wo-1");
  expect(store.activeWorkspace).toBeNull();
  expect(openEditVersionMock).not.toHaveBeenCalled();
  expect(fetchWorkspaceMock).not.toHaveBeenCalled();
});
```

Добавить mismatch test:

```ts
it("keeps the last selection and removes a mismatched workspace marker", async () => {
  sessionStorage.setItem(
    SELECTED_WORK_ORDER_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-2" }),
  );
  sessionStorage.setItem(
    OPENED_WORKSPACE_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: "wo-1",
      code: "WO-001",
      title: "Первый наряд",
      description: null,
      status: "in_progress",
    },
    {
      id: "wo-2",
      code: "WO-002",
      title: "Второй наряд",
      description: null,
      status: "assigned",
    },
  ];

  await store.restoreOpenedWorkspace();

  expect(store.selectedWorkOrderId).toBe("wo-2");
  expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
  expect(fetchWorkspaceMock).not.toHaveBeenCalled();
});
```

Добавить stale-selection test:

```ts
it("clears selection and workspace markers when the saved selection is no longer assigned", async () => {
  sessionStorage.setItem(
    SELECTED_WORK_ORDER_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-missing" }),
  );
  sessionStorage.setItem(
    OPENED_WORKSPACE_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: "wo-1",
      code: "WO-001",
      title: "Первый наряд",
      description: null,
      status: "in_progress",
    },
  ];

  await store.restoreOpenedWorkspace();

  expect(store.selectedWorkOrderId).toBeNull();
  expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBeNull();
  expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
  expect(fetchWorkspaceMock).not.toHaveBeenCalled();
});
```

Добавить table-driven test повреждённых значений:

```ts
it.each([
  "{invalid-json",
  JSON.stringify({}),
  JSON.stringify({ workOrderId: "" }),
  JSON.stringify({ workOrderId: 42 }),
])("removes an invalid selected work order marker: %s", async (storedValue) => {
  sessionStorage.setItem(SELECTED_WORK_ORDER_STORAGE_KEY, storedValue);

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: "wo-1",
      code: "WO-001",
      title: "Первый наряд",
      description: null,
      status: "assigned",
    },
  ];

  await expect(store.restoreOpenedWorkspace()).resolves.toBeUndefined();

  expect(store.selectedWorkOrderId).toBeNull();
  expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBeNull();
  expect(fetchWorkspaceMock).not.toHaveBeenCalled();
});
```

Добавить test, что load failure не уничтожает marker:

```ts
it("keeps the selected marker when assigned work orders fail to load", async () => {
  sessionStorage.setItem(
    SELECTED_WORK_ORDER_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1" }),
  );
  fetchAssignedWorkOrdersMock.mockRejectedValue(networkFailure());

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();

  await store.loadAssigned();

  expect(store.loadError).not.toBeNull();
  expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
    JSON.stringify({ workOrderId: "wo-1" }),
  );
});
```

- [ ] **Step 2: Run the new restore tests and verify failure**

Run:

```powershell
npm test -- src/stores/workOrders.test.ts
```

Expected before implementation:

- selection-only marker does not populate `selectedWorkOrderId`;
- mismatch still restores/fetches `WO-1`;
- stale selected marker remains in storage;
- malformed selected markers are not read or removed by restore.

- [ ] **Step 3: Reconcile selection before restoring workspace**

Рядом с `StoredOpenedWorkspace` добавить:

```ts
type StoredSelectedWorkOrder = {
  workOrderId: string;
};
```

Рядом с selected storage write/clear helpers добавить:

```ts
function readStoredSelectedWorkOrder(): StoredSelectedWorkOrder | null {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<StoredSelectedWorkOrder>;
    if (
      typeof parsed.workOrderId !== "string" ||
      parsed.workOrderId.trim().length === 0
    ) {
      clearStoredSelectedWorkOrder();
      return null;
    }

    return { workOrderId: parsed.workOrderId };
  } catch {
    clearStoredSelectedWorkOrder();
    return null;
  }
}
```

Затем переписать начало `restoreOpenedWorkspace()` и сохранить существующую
error presentation policy. Итоговая action должна иметь следующую структуру:

```ts
async restoreOpenedWorkspace(): Promise<void> {
  if (this.openingWorkOrderId !== null) {
    return;
  }

  const storedSelection = readStoredSelectedWorkOrder();
  const storedWorkspace = readStoredOpenedWorkspace();
  const workOrderId =
    this.selectedWorkOrderId ??
    storedSelection?.workOrderId ??
    storedWorkspace?.workOrderId ??
    null;

  if (!workOrderId) {
    return;
  }

  if (!this.items.some((item) => item.id === workOrderId)) {
    this.selectedWorkOrderId = null;
    clearStoredSelectedWorkOrder();
    this.clearOpenedWorkspace();
    return;
  }

  this.selectedWorkOrderId = workOrderId;
  storeSelectedWorkOrder(workOrderId);

  if (!storedWorkspace) {
    return;
  }

  if (storedWorkspace.workOrderId !== workOrderId) {
    this.clearOpenedWorkspace();
    return;
  }

  if (this.isWorkOrderOpened(workOrderId)) {
    return;
  }

  const editVersionId = storedWorkspace.editVersionId;
  const requestSeq = this.openWorkspaceRequestSeq + 1;
  this.openWorkspaceRequestSeq = requestSeq;
  this.openingWorkOrderId = workOrderId;
  this.openWorkspaceErrorByWorkOrderId = {
    ...this.openWorkspaceErrorByWorkOrderId,
    [workOrderId]: undefined,
  };
  this.openWorkspaceErrorOperationByWorkOrderId = {
    ...this.openWorkspaceErrorOperationByWorkOrderId,
    [workOrderId]: undefined,
  };

  try {
    const workspace = await fetchWorkspace(workOrderId, editVersionId);
    if (
      this.openWorkspaceRequestSeq !== requestSeq ||
      this.selectedWorkOrderId !== workOrderId
    ) {
      return;
    }

    this.updateWorkOrderStatus(workOrderId, workspace.workOrder.status);
    this.openedWorkOrderId = workOrderId;
    this.openedEditVersionId = editVersionId;
    this.workspace = workspace;
    storeOpenedWorkspace({ workOrderId, editVersionId });
    this.openWorkspaceErrorByWorkOrderId = {
      ...this.openWorkspaceErrorByWorkOrderId,
      [workOrderId]: undefined,
    };
    this.openWorkspaceErrorOperationByWorkOrderId = {
      ...this.openWorkspaceErrorOperationByWorkOrderId,
      [workOrderId]: undefined,
    };
  } catch (error: unknown) {
    if (
      this.openWorkspaceRequestSeq === requestSeq &&
      this.selectedWorkOrderId === workOrderId
    ) {
      const parsed = parseApiError(error);
      const errorPresentation = presentWorkspaceRestoreError(parsed);
      this.clearOpenedWorkspace({
        preserveStoredWorkspace: shouldPreserveStoredWorkspace(parsed),
      });
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
        [workOrderId]: errorPresentation ?? undefined,
      };
      this.openWorkspaceErrorOperationByWorkOrderId = {
        ...this.openWorkspaceErrorOperationByWorkOrderId,
        [workOrderId]: errorPresentation ? "restore" : undefined,
      };
    }
  } finally {
    if (
      this.openWorkspaceRequestSeq === requestSeq &&
      this.openingWorkOrderId === workOrderId
    ) {
      this.openingWorkOrderId = null;
    }
  }
},
```

Существующий `retrySelectedWorkspaceError()` продолжает вызывать
`restoreOpenedWorkspace()` для operation `"restore"`; при временной ошибке
opened marker сохранён, поэтому retry повторяет исходный `GET`.

- [ ] **Step 4: Make assigned-list reconciliation clear the selected marker**

В success path `loadAssigned()` заменить ручное обнуление несуществующего
selection:

```ts
if (
  this.selectedWorkOrderId &&
  !this.items.some((item) => item.id === this.selectedWorkOrderId)
) {
  this.clearSelection();
}
```

Оставить отдельную проверку `openedWorkOrderId` для случая, когда selection
существует, но opened state повреждён или устарел.

- [ ] **Step 5: Extend backward-compatibility and race tests**

В существующем test
`"restores opened workspace from session storage without opening edit version again"`
оставить только старый opened marker и добавить:

```ts
expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
  JSON.stringify({ workOrderId: "wo-1" }),
);
```

Добавить restore race:

```ts
it("does not restore an old workspace after the user selects another work order", async () => {
  const deferred = createDeferred<WorkspaceResponse>();
  sessionStorage.setItem(
    SELECTED_WORK_ORDER_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1" }),
  );
  sessionStorage.setItem(
    OPENED_WORKSPACE_STORAGE_KEY,
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );
  fetchWorkspaceMock.mockReturnValue(deferred.promise);

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: "wo-1",
      code: "WO-001",
      title: "Первый наряд",
      description: null,
      status: "in_progress",
    },
    {
      id: "wo-2",
      code: "WO-002",
      title: "Второй наряд",
      description: null,
      status: "assigned",
    },
  ];

  const restoring = store.restoreOpenedWorkspace();
  store.selectWorkOrder("wo-2");
  deferred.resolve(workspaceResponse("wo-1", "ev-1"));
  await restoring;

  expect(store.selectedWorkOrderId).toBe("wo-2");
  expect(store.workspace).toBeNull();
  expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
});
```

- [ ] **Step 6: Add component coverage for preview restore**

Перед component tests заменить разрозненные load/restore вызовы в
`EditorWorkOrdersView.vue` единым helper:

```ts
async function loadAssignedAndRestore(): Promise<void> {
  await workOrders.loadAssigned();
  if (!workOrders.loadError) {
    await workOrders.restoreOpenedWorkspace();
  }
}

onMounted(loadAssignedAndRestore);
```

В `handleLoadErrorAction()` и refresh branch
`handleWorkspaceErrorAction()` вызывать:

```ts
void loadAssignedAndRestore();
```

В template заменить refresh binding:

```vue
@click="loadAssignedAndRestore"
```

Так первоначальный list failure не требует второго reload вкладки: успешный
retry снова выполняет persisted-state reconciliation. Повторный refresh уже
открытого workspace не делает лишний `GET`, потому что
`restoreOpenedWorkspace()` возвращается через `isWorkOrderOpened()`.

В `EditorWorkOrdersView.test.ts` добавить `sessionStorage.clear()` в
`beforeEach()`.

Добавить test с реальной `restoreOpenedWorkspace()` action:

```ts
it("restores the selected work order preview after mount", async () => {
  sessionStorage.setItem(
    "geoservice:selected-work-order",
    JSON.stringify({ workOrderId: "wo-1" }),
  );
  loadAssignedMock.mockResolvedValue(undefined);

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [assignedWorkOrder()];
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);
  await flushPromises();

  expect(store.selectedWorkOrderId).toBe("wo-1");
  expect(
    wrapper.get('[data-test="work-order-wo-1"]').attributes("aria-current"),
  ).toBe("true");
  expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
    "Проверка участка фидера",
  );
  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "empty",
  );
});
```

Добавить test восстановления после list retry:

```ts
it("restores the selected preview after retrying the assigned list", async () => {
  sessionStorage.setItem(
    "geoservice:selected-work-order",
    JSON.stringify({ workOrderId: "wo-1" }),
  );

  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.loadError = {
    summary: "Не удалось загрузить назначенные наряды.",
    guidance: "Проверьте соединение и повторите запрос.",
    action: { id: "retry", label: "Повторить" },
    diagnostics: { code: "INTERNAL_ERROR", correlationId: "list-id" },
  };
  let loadCount = 0;
  store.loadAssigned = vi.fn(async () => {
    loadCount += 1;
    if (loadCount === 2) {
      store.items = [assignedWorkOrder()];
      store.loadError = null;
    }
  });

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);
  await flushPromises();

  await wrapper.get('[data-test="error-action"]').trigger("click");
  await flushPromises();

  expect(store.selectedWorkOrderId).toBe("wo-1");
  expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
    "Проверка участка фидера",
  );
});
```

Заменить устаревший test
`"returns to the saved workspace when its work order is selected again"` на
новый contract:

```ts
it("shows preview instead of a cached workspace after switching away and back", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    inProgressWorkOrder(),
    {
      id: "wo-2",
      code: "WO-002",
      title: "Второй наряд",
      description: null,
      status: "assigned",
    },
  ];
  store.selectWorkOrder("wo-1");
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = workspaceResponse();
  sessionStorage.setItem(
    "geoservice:opened-workspace",
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );
  store.loadAssigned = loadAssignedMock;
  loadAssignedMock.mockResolvedValue(undefined);

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);
  await flushPromises();

  await wrapper.get('[data-test="work-order-wo-2"]').trigger("click");
  await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

  expect(store.workspace).toBeNull();
  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "empty",
  );
  expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(
    true,
  );
});
```

- [ ] **Step 7: Run Task 2 tests**

Run:

```powershell
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts
npm run typecheck
```

Expected: both commands exit `0`; selection-only reload renders preview,
mismatched markers do not call `fetchWorkspace`, and old opened-only tabs
still restore.

- [ ] **Step 8: Review checkpoint**

Inspect:

```powershell
git diff --check -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts apps/frontend/src/components/EditorWorkOrdersView.vue apps/frontend/src/components/EditorWorkOrdersView.test.ts
git diff -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts apps/frontend/src/components/EditorWorkOrdersView.vue apps/frontend/src/components/EditorWorkOrdersView.test.ts
```

Expected: no workspace data is retained by selection switching; no
`POST /edit-versions` was added to reload restoration. Leave changes unstaged.

---

### Task 3: Preserve Or Clear Both Markers With The Auth Session

**Files:**

- Modify: `apps/frontend/src/stores/auth.test.ts:54-95`
- Modify: `apps/frontend/src/stores/auth.test.ts:118-310`
- Modify: `apps/frontend/src/stores/auth.ts:41-70`
- Modify: `apps/frontend/src/stores/auth.ts:106-116`

**Interfaces:**

- Consumes:
  - `ResetWorkOrdersOptions.preserveOpenedWorkspace?: boolean`;
  - `ResetWorkOrdersOptions.preserveSelectedWorkOrder?: boolean`.
- Produces:
  - `SetAuthOptions.preserveWorkOrderStateOnInitialUser?: boolean`;
  - initial `restoreSession()` passes both preserve flags;
  - all logout, unauthorized and user-change paths call reset without
    preservation and therefore clear both markers.

- [ ] **Step 1: Update the auth test double and add failing lifecycle assertions**

В `auth.test.ts` добавить:

```ts
const SELECTED_WORK_ORDER_STORAGE_KEY =
  "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";
```

Заменить `resetWorkOrdersMock.mockImplementation`:

```ts
resetWorkOrdersMock.mockImplementation(
  (options?: {
    preserveOpenedWorkspace?: boolean;
    preserveSelectedWorkOrder?: boolean;
  }) => {
    if (!options?.preserveOpenedWorkspace) {
      sessionStorage.removeItem(OPENED_WORKSPACE_STORAGE_KEY);
    }
    if (!options?.preserveSelectedWorkOrder) {
      sessionStorage.removeItem(SELECTED_WORK_ORDER_STORAGE_KEY);
    }
  },
);
```

Переименовать initial restore test в
`"preserves work order session markers when restoreSession hydrates initial user"`,
записать оба markers и ожидать:

```ts
expect(resetWorkOrdersMock).toHaveBeenCalledWith({
  preserveOpenedWorkspace: true,
  preserveSelectedWorkOrder: true,
});
expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
  JSON.stringify({ workOrderId: "wo-1" }),
);
expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBe(
  JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
);
```

В test `"clearLocalSession clears memory without calling backend logout"`
до вызова action записать оба markers, а после вызова проверить:

```ts
expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBeNull();
expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
```

- [ ] **Step 2: Run auth tests and verify the preserve assertion fails**

Run:

```powershell
npm test -- src/stores/auth.test.ts
```

Expected before implementation: initial restore passes only
`preserveOpenedWorkspace: true`; selected marker is removed by the reset mock.

- [ ] **Step 3: Extend auth preservation options**

В `auth.ts` заменить option type:

```ts
type SetAuthOptions = {
  preserveWorkOrderStateOnInitialUser?: boolean;
};
```

В `setAuth()` вычислить единое условие и передать оба flags:

```ts
const preserveWorkOrderState =
  options.preserveWorkOrderStateOnInitialUser === true &&
  previousUserId === null;

resetWorkOrdersIfUserIdChanged(previousUserId, user.id, {
  preserveOpenedWorkspace: preserveWorkOrderState,
  preserveSelectedWorkOrder: preserveWorkOrderState,
});
```

В `restoreSession()` заменить option:

```ts
this.setAuth(result.access_token, result.user, {
  preserveWorkOrderStateOnInitialUser: true,
});
```

Не передавать preserve option из `loginWithPassword()`: новый login обязан
очистить markers предыдущей или анонимной browser state.

- [ ] **Step 4: Cover user replacement and same-user refresh**

В test `"resets work orders when setAuth changes user id"` записать оба
markers до `setAuth()` и после вызова проверить, что reset mock удалил их.

В test
`"does not reset work orders when restoreSession refreshes the same user id"`
записать оба markers, затем проверить:

```ts
expect(resetWorkOrdersMock).not.toHaveBeenCalled();
expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).not.toBeNull();
expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).not.toBeNull();
```

- [ ] **Step 5: Run Task 3 tests**

Run:

```powershell
npm test -- src/stores/auth.test.ts src/stores/workOrders.test.ts
npm run typecheck
```

Expected: commands exit `0`; initial restore preserves both markers, while
logout and user id changes remove both.

- [ ] **Step 6: Review checkpoint**

Inspect:

```powershell
git diff --check -- apps/frontend/src/stores/auth.ts apps/frontend/src/stores/auth.test.ts
git diff -- apps/frontend/src/stores/auth.ts apps/frontend/src/stores/auth.test.ts
```

Expected: auth changes only coordinate work-order persisted state and do not
introduce token storage. Leave changes unstaged.

---

### Task 4: Full Frontend Verification And Manual Acceptance

**Files:**

- Verify:
  - `apps/frontend/src/stores/workOrders.ts`
  - `apps/frontend/src/stores/workOrders.test.ts`
  - `apps/frontend/src/stores/auth.ts`
  - `apps/frontend/src/stores/auth.test.ts`
  - `apps/frontend/src/components/EditorWorkOrdersView.vue`
  - `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
- Reference:
  - `docs/superpowers/specs/2026-07-25-work-order-selection-reload-design.md`

**Interfaces:**

- Consumes: completed Tasks 1-3.
- Produces: verified unstaged implementation ready for user review.

- [ ] **Step 1: Run all frontend automated checks**

Run from `apps/frontend`:

```powershell
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```

Expected: every command exits `0`; Vitest reports no failed tests; TypeScript,
ESLint, Prettier and production build complete without errors.

- [ ] **Step 2: Run diff validation**

Run from repository root:

```powershell
git diff --check
git status --short
```

Expected: `git diff --check` has no output. `git status --short` lists only the
approved design, this plan and implementation files changed by Tasks 1-3,
plus any pre-existing unrelated user changes that must remain untouched.

- [ ] **Step 3: Start the existing demo environment for manual acceptance**

Run from `infra` in a dedicated terminal:

```powershell
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```

Wait until backend and `frontend-dev` are healthy, then open
`http://localhost:5173` and sign in as:

```text
alexey.editor@example.local
alexey-editor-password
```

- [ ] **Step 4: Verify selection-only reload**

1. Select a WorkOrder without pressing `Начать` or `Продолжить`.
2. Confirm that its preview panel is visible.
3. Reload the same browser tab.
4. Confirm that the same WorkOrder has `aria-current`, the same preview panel
   is visible, and the map remains in empty mode.

- [ ] **Step 5: Verify matching opened workspace reload**

1. Press `Начать` or `Продолжить` for the selected WorkOrder.
2. Confirm that workspace metadata and map appear.
3. Reload the same tab.
4. Confirm that the workspace returns without creating another
   `EditVersion`; browser network traffic contains workspace `GET` and no
   reload-triggered `POST /edit-versions`.

- [ ] **Step 6: Verify switching clears the client workspace**

Canonical demo seed гарантирует только `WO-001`. Если текущая база содержит
второй WorkOrder, назначенный тому же Editor:

1. With `WO-001` workspace open, select the second assigned WorkOrder.
2. Confirm that the second WorkOrder preview appears and the old map
   disappears.
3. Reload the tab.
4. Confirm that the second WorkOrder remains selected and no workspace request
   for `WO-001` is sent.
5. Select `WO-001` again.
6. Confirm that only its preview appears until `Продолжить` is pressed.

Если второго назначенного WorkOrder нет, отметить этот manual step как
`not applicable: canonical seed has one WorkOrder`; обязательным evidence
остаются passing tests
`"evicts the client workspace when another work order is selected"`,
`"keeps the last selection and removes a mismatched workspace marker"` и
`"shows preview instead of a cached workspace after switching away and back"`.

- [ ] **Step 7: Stop the foreground demo environment**

In the dedicated compose terminal press `Ctrl+C`. Do not run `down -v`; the
manual check does not authorize deletion of local database volumes.

- [ ] **Step 8: Final review handoff**

Report:

- automated commands and their final pass/fail result;
- manual scenarios and observed result;
- exact unstaged files changed;
- confirmation that backend/API were untouched;
- confirmation that no agent memory update is needed because the approved
  design and implementation tests preserve the durable behavior.

Do not stage, commit or push. The user performs all Git write operations.
