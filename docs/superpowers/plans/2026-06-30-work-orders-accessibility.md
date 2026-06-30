# Work Orders Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить accessibility-семантику для состояний списка, выбранного наряда и ошибок на экране `Мои наряды`.

**Architecture:** Изменение остается локальным для `EditorWorkOrdersView.vue`: текущий `ul/li` список и `button`-действия сохраняются, а недостающие состояния передаются через ARIA-атрибуты. Тесты компонента фиксируют семантический контракт: спокойные live regions для обычных состояний, `role="alert"` для ошибок, `aria-current="true"` для выбранного наряда и отсутствие `aria-pressed`.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vitest, Vue Test Utils.

---

## File Structure

- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
  - Добавляет component tests для `aria-live`, `aria-atomic`, `role="alert"`, `aria-current` и отсутствия `aria-pressed`.
  - Расширяет существующий тест ошибки открытия наряда проверкой `role="alert"`.

- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`
  - Добавляет `aria-live="polite"` и `aria-atomic="true"` для loading и empty states.
  - Добавляет `role="alert"` на текст общей ошибки загрузки списка.
  - Добавляет `aria-current="true"` на кнопку выбранного наряда.
  - Добавляет `role="alert"` на ошибку открытия конкретного наряда.

## Task 1: Accessibility Tests

**Files:**
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`

- [ ] **Step 1: Add failing tests for list state announcements**

Add these tests inside `describe("EditorWorkOrdersView", () => { ... })`, after the existing `"loads work orders and renders empty map mode"` test:

```ts
  it("announces list loading state politely", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.isLoading = true;
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const state = wrapper.get(".panelState");
    expect(state.text()).toContain("Загружаем назначенные наряды");
    expect(state.attributes("aria-live")).toBe("polite");
    expect(state.attributes("aria-atomic")).toBe("true");
  });

  it("announces the empty assigned list politely", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const state = wrapper.get(".panelState");
    expect(state.text()).toContain("Назначенных нарядов нет.");
    expect(state.attributes("aria-live")).toBe("polite");
    expect(state.attributes("aria-atomic")).toBe("true");
  });
```

- [ ] **Step 2: Run the list state tests and verify they fail**

Run from `apps/frontend`:

```powershell
npm run test -- src/components/EditorWorkOrdersView.test.ts -t "announces"
```

Expected: FAIL. The rendered `.panelState` elements do not yet have `aria-live` or `aria-atomic`.

- [ ] **Step 3: Add failing tests for error alerts and selected work order semantics**

Add these tests inside `describe("EditorWorkOrdersView", () => { ... })`, after the existing `"selects and highlights a work order locally"` test:

```ts
  it("marks list load errors as alerts", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.errorMessage =
      "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.";
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const errorMessage = wrapper.get(".panelState.isError span");
    expect(errorMessage.text()).toContain(
      "Не удалось загрузить назначенные наряды",
    );
    expect(errorMessage.attributes("role")).toBe("alert");
  });

  it("exposes the selected work order as current without pressed state", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      assignedWorkOrder(),
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.selectedWorkOrderId = "wo-1";
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const selected = wrapper.get('[data-test="work-order-wo-1"]');
    const unselected = wrapper.get('[data-test="work-order-wo-2"]');

    expect(selected.attributes("aria-current")).toBe("true");
    expect(selected.attributes("aria-pressed")).toBeUndefined();
    expect(unselected.attributes("aria-current")).toBeUndefined();
    expect(unselected.attributes("aria-pressed")).toBeUndefined();
  });
```

- [ ] **Step 4: Extend the existing open error test with alert semantics**

In the existing `"shows open error near selected work order"` test, replace the final assertion block:

```ts
    expect(
      wrapper.get('[data-test="open-work-order-error-wo-1"]').text(),
    ).toContain("Не удалось открыть рабочую версию");
```

with:

```ts
    const openError = wrapper.get(
      '[data-test="open-work-order-error-wo-1"]',
    );
    expect(openError.text()).toContain("Не удалось открыть рабочую версию");
    expect(openError.attributes("role")).toBe("alert");
```

- [ ] **Step 5: Run the new semantic tests and verify they fail**

Run from `apps/frontend`:

```powershell
npm run test -- src/components/EditorWorkOrdersView.test.ts -t "alert|current|open error"
```

Expected: FAIL. The error elements do not yet have `role="alert"`, and work order buttons do not yet expose `aria-current`.

## Task 2: Template ARIA Semantics

**Files:**
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`

- [ ] **Step 1: Add polite live region attributes to loading and empty states**

In `apps/frontend/src/components/EditorWorkOrdersView.vue`, replace the loading state block:

```vue
      <div v-if="workOrders.isLoading" class="panelState">
        Загружаем назначенные наряды...
      </div>
```

with:

```vue
      <div
        v-if="workOrders.isLoading"
        class="panelState"
        aria-live="polite"
        aria-atomic="true"
      >
        Загружаем назначенные наряды...
      </div>
```

Replace the empty state block:

```vue
      <div v-else-if="workOrders.items.length === 0" class="panelState">
        Назначенных нарядов нет.
      </div>
```

with:

```vue
      <div
        v-else-if="workOrders.items.length === 0"
        class="panelState"
        aria-live="polite"
        aria-atomic="true"
      >
        Назначенных нарядов нет.
      </div>
```

- [ ] **Step 2: Add alert semantics to the list load error text**

In the same file, replace the list load error block:

```vue
      <div v-else-if="workOrders.errorMessage" class="panelState isError">
        <span>{{ workOrders.errorMessage }}</span>
        <button
          class="retryButton"
          type="button"
          @click="workOrders.loadAssigned"
        >
          Повторить
        </button>
      </div>
```

with:

```vue
      <div v-else-if="workOrders.errorMessage" class="panelState isError">
        <span role="alert">{{ workOrders.errorMessage }}</span>
        <button
          class="retryButton"
          type="button"
          @click="workOrders.loadAssigned"
        >
          Повторить
        </button>
      </div>
```

The `role="alert"` stays on the text node wrapper, while the retry button remains a normal button outside the alert semantics.

- [ ] **Step 3: Add current-state semantics to selected work order buttons**

In the work order selection button, replace:

```vue
            <button
              class="workOrderButton"
              type="button"
              :data-test="`work-order-${workOrder.id}`"
              @click="workOrders.selectWorkOrder(workOrder.id)"
            >
```

with:

```vue
            <button
              class="workOrderButton"
              type="button"
              :aria-current="
                workOrders.selectedWorkOrderId === workOrder.id
                  ? 'true'
                  : undefined
              "
              :data-test="`work-order-${workOrder.id}`"
              @click="workOrders.selectWorkOrder(workOrder.id)"
            >
```

Do not add `aria-pressed`. The button selects the current work order; it does not toggle an on/off state.

- [ ] **Step 4: Add alert semantics to per-work-order open errors**

In the work order open error block, replace:

```vue
            <div
              v-if="openError(workOrder.id)"
              class="workOrderError"
              :data-test="`open-work-order-error-${workOrder.id}`"
            >
              {{ openError(workOrder.id) }}
            </div>
```

with:

```vue
            <div
              v-if="openError(workOrder.id)"
              class="workOrderError"
              role="alert"
              :data-test="`open-work-order-error-${workOrder.id}`"
            >
              {{ openError(workOrder.id) }}
            </div>
```

- [ ] **Step 5: Run the focused component tests and verify they pass**

Run from `apps/frontend`:

```powershell
npm run test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS. All `EditorWorkOrdersView` tests pass, including the new accessibility assertions.

## Task 3: Regression Checks And Handoff

**Files:**
- Check: `apps/frontend/src/components/EditorWorkOrdersView.vue`
- Check: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`

- [ ] **Step 1: Run frontend typecheck**

Run from `apps/frontend`:

```powershell
npm run typecheck
```

Expected: PASS. `vue-tsc --noEmit` completes without TypeScript or Vue template errors.

- [ ] **Step 2: Run the final focused regression gate**

Run from `apps/frontend`:

```powershell
npm run test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS. The component test file passes after typecheck.

- [ ] **Step 3: Review the final diff**

Run from repository root:

```powershell
git diff -- apps/frontend/src/components/EditorWorkOrdersView.vue apps/frontend/src/components/EditorWorkOrdersView.test.ts
```

Expected: The diff only changes `EditorWorkOrdersView.vue` and `EditorWorkOrdersView.test.ts`. It must not change `LoginScreen.vue`, `MapView.vue`, Pinia stores, backend files, API contracts, visual CSS, or the work order selection behavior.

- [ ] **Step 4: Commit the implementation when git operations are approved**

Run from repository root:

```powershell
git add -- apps/frontend/src/components/EditorWorkOrdersView.vue apps/frontend/src/components/EditorWorkOrdersView.test.ts
git commit -m "feat: add work orders accessibility semantics"
```

Expected: A commit is created containing only the component and component test changes.

## Memory And Wiki Decision

This implementation should not update agent memory or `Code_wiki` by default. The change is local UI semantics already preserved by code, tests, and the design/implementation plan. Reconsider durable memory only if implementation uncovers a non-obvious accessibility pattern that should apply across multiple future screens.
