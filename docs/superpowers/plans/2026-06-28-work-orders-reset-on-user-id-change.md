# WorkOrders Reset On User Id Change Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить `workOrders.reset()` и вызывать его только при фактическом изменении `auth.user.id`.

**Architecture:** `workOrders` остается владельцем user-scoped состояния и получает явный `reset()`. `auth` остается источником identity и вызывает reset через сравнение `previousUserId` и `nextUserId`, не привязываясь к факту `restoreSession()` как событию. Async responses в `workOrders` защищаются request sequence, чтобы старые ответы не восстанавливали данные после reset.

**Tech Stack:** Vue 3, Pinia, TypeScript, Vitest, Axios auth interceptor.

---

## File Structure

- Modify: `apps/frontend/src/stores/workOrders.ts`
  - Добавляет фабрику начального состояния.
  - Добавляет `reset()`.
  - Добавляет `loadAssignedRequestSeq`.
  - Инвалидирует pending `loadAssigned()` и `openSelectedWorkOrder()` responses.

- Modify: `apps/frontend/src/stores/workOrders.test.ts`
  - Покрывает очистку user-scoped state.
  - Покрывает stale response после reset для списка assigned work orders.
  - Покрывает stale response после reset для открытия workspace.

- Modify: `apps/frontend/src/stores/auth.ts`
  - Импортирует `useWorkOrdersStore`.
  - Добавляет helper сравнения user id.
  - Вызывает `workOrders.reset()` только при `previousUserId !== nextUserId`.

- Modify: `apps/frontend/src/stores/auth.test.ts`
  - Мокает `workOrders.reset()`.
  - Покрывает logout, setAuth/login и restoreSession сценарии с тем же и другим user id.

## Task 1: WorkOrders Reset API

**Files:**
- Modify: `apps/frontend/src/stores/workOrders.test.ts`
- Modify: `apps/frontend/src/stores/workOrders.ts`

- [ ] **Step 1: Write the failing reset test**

Add this test inside `describe("work orders store", () => { ... })` in `apps/frontend/src/stores/workOrders.test.ts`:

```ts
  it("resets user-scoped state and invalidates pending requests", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Assigned work",
        description: "Old user work order",
        status: "assigned",
      },
    ];
    store.isLoading = true;
    store.errorMessage = "load failed";
    store.selectedWorkOrderId = "wo-1";
    store.openedWorkOrderId = "wo-1";
    store.openedEditVersionId = "ev-1";
    store.workspace = workspaceResponse();
    store.isOpeningWorkspace = true;
    store.openWorkspaceErrorByWorkOrderId = {
      "wo-1": "open failed",
    };
    store.lastFittedWorkspaceKey = "wo-1:ev-1";
    store.openWorkspaceRequestSeq = 7;
    store.loadAssignedRequestSeq = 11;

    store.reset();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBeNull();
    expect(store.selectedWorkOrderId).toBeNull();
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.openedEditVersionId).toBeNull();
    expect(store.workspace).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
    expect(store.openWorkspaceErrorByWorkOrderId).toEqual({});
    expect(store.lastFittedWorkspaceKey).toBeNull();
    expect(store.openWorkspaceRequestSeq).toBe(8);
    expect(store.loadAssignedRequestSeq).toBe(12);
  });
```

- [ ] **Step 2: Run the failing reset test**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/workOrders.test.ts -t "resets user-scoped state"
```

Expected: FAIL because `reset()` and `loadAssignedRequestSeq` do not exist yet.

- [ ] **Step 3: Implement the initial state factory and reset action**

In `apps/frontend/src/stores/workOrders.ts`, replace the inline `state` factory with a reusable function and add `loadAssignedRequestSeq`.

Use this state type:

```ts
type WorkOrdersState = {
  items: WorkOrderSummary[];
  isLoading: boolean;
  errorMessage: string | null;
  selectedWorkOrderId: string | null;
  openedWorkOrderId: string | null;
  openedEditVersionId: string | null;
  workspace: WorkspaceResponse | null;
  isOpeningWorkspace: boolean;
  openWorkspaceErrorByWorkOrderId: Record<string, string | undefined>;
  lastFittedWorkspaceKey: string | null;
  loadAssignedRequestSeq: number;
  openWorkspaceRequestSeq: number;
};
```

Add this helper above `export const useWorkOrdersStore`:

```ts
function createInitialWorkOrdersState(): WorkOrdersState {
  return {
    items: [],
    isLoading: false,
    errorMessage: null,
    selectedWorkOrderId: null,
    openedWorkOrderId: null,
    openedEditVersionId: null,
    workspace: null,
    isOpeningWorkspace: false,
    openWorkspaceErrorByWorkOrderId: {},
    lastFittedWorkspaceKey: null,
    loadAssignedRequestSeq: 0,
    openWorkspaceRequestSeq: 0,
  };
}
```

Change the store state:

```ts
state: createInitialWorkOrdersState,
```

Add this action before `loadAssigned()`:

```ts
    reset(): void {
      const nextLoadAssignedRequestSeq = this.loadAssignedRequestSeq + 1;
      const nextOpenWorkspaceRequestSeq = this.openWorkspaceRequestSeq + 1;

      this.$patch({
        ...createInitialWorkOrdersState(),
        loadAssignedRequestSeq: nextLoadAssignedRequestSeq,
        openWorkspaceRequestSeq: nextOpenWorkspaceRequestSeq,
      });
    },
```

- [ ] **Step 4: Run the reset test again**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/workOrders.test.ts -t "resets user-scoped state"
```

Expected: PASS.

## Task 2: WorkOrders Async Safety After Reset

**Files:**
- Modify: `apps/frontend/src/stores/workOrders.test.ts`
- Modify: `apps/frontend/src/stores/workOrders.ts`

- [ ] **Step 1: Add a deferred promise helper and failing stale-response tests**

Add this helper near the existing response helpers in `apps/frontend/src/stores/workOrders.test.ts`:

```ts
function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}
```

Add these tests inside `describe("work orders store", () => { ... })`:

```ts
  it("ignores assigned work orders response after reset", async () => {
    const assignedResponse = {
      workOrders: [
        {
          id: "wo-1",
          code: "WO-001",
          title: "Old user work order",
          description: null,
          status: "assigned" as const,
        },
      ],
    };
    const assignedDeferred = createDeferred<typeof assignedResponse>();
    fetchAssignedWorkOrdersMock.mockReturnValue(assignedDeferred.promise);

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    const loading = store.loadAssigned();
    expect(store.isLoading).toBe(true);

    store.reset();
    assignedDeferred.resolve(assignedResponse);
    await loading;

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBeNull();
  });

  it("ignores open workspace response after reset", async () => {
    const openResponse = openEditVersionResponse();
    const openDeferred = createDeferred<typeof openResponse>();
    openEditVersionMock.mockReturnValue(openDeferred.promise);
    fetchWorkspaceMock.mockResolvedValue(workspaceResponse());

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Old user work order",
        description: null,
        status: "assigned",
      },
    ];
    store.selectWorkOrder("wo-1");

    const opening = store.openSelectedWorkOrder();
    expect(store.isOpeningWorkspace).toBe(true);

    store.reset();
    openDeferred.resolve(openResponse);
    await opening;

    expect(fetchWorkspaceMock).not.toHaveBeenCalled();
    expect(store.items).toEqual([]);
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.openedEditVersionId).toBeNull();
    expect(store.workspace).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
  });
```

- [ ] **Step 2: Run the stale-response tests and verify they fail**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/workOrders.test.ts -t "after reset"
```

Expected: FAIL because `loadAssigned()` still writes stale responses and `openSelectedWorkOrder()` can continue after reset.

- [ ] **Step 3: Guard `loadAssigned()` by request sequence**

Replace `loadAssigned()` in `apps/frontend/src/stores/workOrders.ts` with:

```ts
    async loadAssigned() {
      const requestSeq = this.loadAssignedRequestSeq + 1;
      this.loadAssignedRequestSeq = requestSeq;
      this.isLoading = true;
      this.errorMessage = null;
      try {
        const result = await fetchAssignedWorkOrders();
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

        this.items = result.workOrders;
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        ) {
          this.selectedWorkOrderId = null;
          this.clearOpenedWorkspace();
        }
        if (
          this.openedWorkOrderId &&
          !this.items.some((item) => item.id === this.openedWorkOrderId)
        ) {
          this.clearOpenedWorkspace();
        }
      } catch {
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

        this.items = [];
        this.errorMessage =
          "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.";
      } finally {
        if (this.loadAssignedRequestSeq === requestSeq) {
          this.isLoading = false;
        }
      }
    },
```

- [ ] **Step 4: Guard `openSelectedWorkOrder()` before local state updates**

In `apps/frontend/src/stores/workOrders.ts`, inside `openSelectedWorkOrder()`, add this guard immediately after `const openResult = await openEditVersion(workOrderId);`:

```ts
        if (
          this.openWorkspaceRequestSeq !== requestSeq ||
          this.selectedWorkOrderId !== workOrderId
        ) {
          return;
        }
```

The beginning of the `try` block should become:

```ts
      try {
        const openResult = await openEditVersion(workOrderId);
        if (
          this.openWorkspaceRequestSeq !== requestSeq ||
          this.selectedWorkOrderId !== workOrderId
        ) {
          return;
        }

        this.updateWorkOrderStatus(workOrderId, "in_progress");

        const editVersionId = openResult.editVersion.id;
        const workspace = await fetchWorkspace(workOrderId, editVersionId);
```

- [ ] **Step 5: Run workOrders store tests**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/workOrders.test.ts
```

Expected: PASS for all `workOrders` store tests.

## Task 3: Auth Identity-Gated Reset

**Files:**
- Modify: `apps/frontend/src/stores/auth.test.ts`
- Modify: `apps/frontend/src/stores/auth.ts`

- [ ] **Step 1: Mock `workOrders.reset()` in auth tests**

In `apps/frontend/src/stores/auth.test.ts`, add this mock near the existing auth API mocks:

```ts
const resetWorkOrdersMock = vi.hoisted(() => vi.fn());

vi.mock("@/stores/workOrders", () => ({
  useWorkOrdersStore: () => ({
    reset: resetWorkOrdersMock,
  }),
}));
```

Keep the existing `beforeEach()` with `vi.clearAllMocks()` so `resetWorkOrdersMock` is cleared before every test.

- [ ] **Step 2: Add failing logout and setAuth tests**

Add these tests inside `describe("auth store", () => { ... })`:

```ts
  it("resets work orders on logout only when user id changes to null", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    store.logout();
    store.logout();

    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("does not reset work orders when setAuth keeps the same user id", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "old@example.com",
      role: "editor",
    };

    store.setAuth("token-2", {
      id: "user-1",
      email: "new-email@example.com",
      role: "editor",
    });

    expect(resetWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("resets work orders when setAuth changes user id", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    store.setAuth("token-2", {
      id: "user-2",
      email: "other-editor@example.com",
      role: "editor",
    });

    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });
```

- [ ] **Step 3: Add failing restoreSession tests**

Add these tests inside `describe("auth store", () => { ... })`:

```ts
  it("does not reset work orders when restoreSession confirms the same user id", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "user-1",
        email: "cached@example.com",
        role: "editor",
      }),
    );
    fetchMeMock.mockResolvedValue({
      user: {
        id: "user-1",
        email: "fresh@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.user?.id).toBe("user-1");
    expect(resetWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("resets work orders when restoreSession returns a different user id", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "user-1",
        email: "cached@example.com",
        role: "editor",
      }),
    );
    fetchMeMock.mockResolvedValue({
      user: {
        id: "user-2",
        email: "fresh@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.user?.id).toBe("user-2");
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("does not reset work orders when restoreSession fails without changing user id", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "user-1",
        email: "cached@example.com",
        role: "editor",
      }),
    );
    fetchMeMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 503 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.user?.id).toBe("user-1");
    expect(resetWorkOrdersMock).not.toHaveBeenCalled();
  });
```

- [ ] **Step 4: Run auth tests and verify they fail**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/auth.test.ts
```

Expected: FAIL because `auth` does not call `workOrders.reset()` yet.

- [ ] **Step 5: Implement identity-gated reset in auth store**

In `apps/frontend/src/stores/auth.ts`, add the store import:

```ts
import { useWorkOrdersStore } from "@/stores/workOrders";
```

Add these helpers above `export const useAuthStore`:

```ts
function authUserId(user: AuthUser | null): string | null {
  return user?.id ?? null;
}

function resetWorkOrdersIfUserIdChanged(
  previousUserId: string | null,
  nextUserId: string | null,
): void {
  if (previousUserId === nextUserId) {
    return;
  }

  useWorkOrdersStore().reset();
}
```

Update `setAuth()`:

```ts
      setAuth(token: string, user: AuthUser) {
        const previousUserId = authUserId(this.user);

        this.token = token;
        this.user = user;
        this.sessionError = null;
        localStorage.setItem(ACCESS_TOKEN_KEY, token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        resetWorkOrdersIfUserIdChanged(previousUserId, user.id);
      },
```

Update `setUser()`:

```ts
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);

        this.user = user;
        if (user) {
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        } else {
          localStorage.removeItem(AUTH_USER_KEY);
        }

        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
      },
```

Update `logout()`:

```ts
      logout() {
        const previousUserId = authUserId(this.user);

        this.token = null;
        this.user = null;
        this.sessionError = null;
        this.isReady = true;
        this.isRestoring = false;
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(AUTH_USER_KEY);
        resetWorkOrdersIfUserIdChanged(previousUserId, null);
      },
```

- [ ] **Step 6: Run auth tests**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/auth.test.ts
```

Expected: PASS for all `auth` store tests.

## Task 4: Regression Verification

**Files:**
- Verify: `apps/frontend/src/stores/workOrders.ts`
- Verify: `apps/frontend/src/stores/auth.ts`
- Verify: `apps/frontend/src/stores/workOrders.test.ts`
- Verify: `apps/frontend/src/stores/auth.test.ts`

- [ ] **Step 1: Run the focused store test suite**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/stores/workOrders.test.ts src/stores/auth.test.ts
```

Expected: PASS.

- [ ] **Step 2: Run the frontend typecheck**

Run from `apps/frontend`:

```powershell
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 3: Run the frontend test suite**

Run from `apps/frontend`:

```powershell
npm run test
```

Expected: PASS.

- [ ] **Step 4: Check repository diff**

Run from repository root:

```powershell
git status --short
git diff -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts apps/frontend/src/stores/auth.ts apps/frontend/src/stores/auth.test.ts
```

Expected: only the intended frontend store and test files are modified.

- [ ] **Step 5: Decide on durable memory and repository-change ingest**

Do not write agent memory for this change unless implementation reveals a non-obvious bug root cause or durable project pattern not already captured by the spec and code.

Do not run `/ingest repository-change` unless the final implementation adds durable technical knowledge beyond the code and the accepted spec. A small identity-gated reset in frontend stores is expected to be self-documenting through tests and the design spec.
