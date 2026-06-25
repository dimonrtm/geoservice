# Edit Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать frontend-переход из выбранного `WorkOrder` в read-only `Edit Workspace` с `AOI`, сетью и состоянием `EditVersion`.

**Architecture:** Backend contract уже существует, поэтому работа сосредоточена на frontend. `workOrdersStore` управляет списком, выбранным work order и открытым workspace; `EditorWorkOrdersView` показывает action-кнопку только у выбранного неоткрытого work order; `MapView mode="workspace"` отрисовывает read-only AOI/features через отдельный map helper и не включает legacy layer editing.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vite/Vitest, MapLibre GL, Axios, existing FastAPI Work Orders API.

---

## File Structure

- Modify `apps/frontend/src/contracts/work-orders.ts` - добавить DTO для `POST /edit-versions` и `GET /workspace`.
- Modify `apps/frontend/src/api/workOrders.ts` - добавить `openEditVersion()` и `fetchWorkspace()`.
- Modify `apps/frontend/src/stores/workOrders.ts` - добавить состояние открытия workspace, error state, stale-response guard и getters.
- Modify `apps/frontend/src/stores/workOrders.test.ts` - покрыть open flow, errors и stale response.
- Modify `apps/frontend/src/components/EditorWorkOrdersView.vue` - добавить `Начать` / `Продолжить`, ошибку у выбранного work order и workspace map mode.
- Modify `apps/frontend/src/components/EditorWorkOrdersView.test.ts` - покрыть action-кнопки, исчезновение кнопки, error state и `MapView mode`.
- Create `apps/frontend/src/map/workspace-layers.ts` - изолированная MapLibre отрисовка AOI/features и fit-to-AOI.
- Create `apps/frontend/src/map/workspace-layers.test.ts` - unit tests для sources/layers/data/fitBounds без настоящего браузерного MapLibre.
- Modify `apps/frontend/src/components/MapView.vue` - добавить `mode="workspace"`, props для workspace и fit-key, emit `workspaceFitted`.
- Modify `apps/frontend/src/components/MapView.test.ts` - проверить, что workspace mode не вызывает legacy loading/realtime/editing и вызывает workspace helper.
- Modify `docs/release_1/sprint_1/README.md` - добавить ссылку на implementation plan.
- Modify `docs/agent-memory/file-map.md` - добавить компактную навигацию для Интенсива 12.

План не требует backend-кода, миграций или seed changes.

## Task 1: Store Tests For Opening Workspace

**Files:**
- Modify: `apps/frontend/src/stores/workOrders.test.ts`
- Later modify: `apps/frontend/src/stores/workOrders.ts`
- Later modify: `apps/frontend/src/api/workOrders.ts`
- Later modify: `apps/frontend/src/contracts/work-orders.ts`

- [ ] **Step 1: Extend API mocks in the store test**

Replace the current mock block in `apps/frontend/src/stores/workOrders.test.ts` with:

```ts
const fetchAssignedWorkOrdersMock = vi.fn();
const openEditVersionMock = vi.fn();
const fetchWorkspaceMock = vi.fn();

vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
  openEditVersion: openEditVersionMock,
  fetchWorkspace: fetchWorkspaceMock,
}));
```

Add helpers below the `vi.mock` block:

```ts
function openEditVersionResponse(workOrderId = "wo-1") {
  return {
    created: true,
    editVersion: {
      id: "ev-1",
      workOrderId,
      ownerId: "user-1",
      status: "open",
      baseNetworkRevision: 1,
      createdAt: "2026-06-25T08:00:00Z",
      lastOpenedAt: "2026-06-25T08:00:00Z",
    },
  };
}

function workspaceResponse(workOrderId = "wo-1", editVersionId = "ev-1") {
  return {
    workOrder: {
      id: workOrderId,
      code: "WO-001",
      title: "Проверка участка фидера",
      description: "Описание",
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: editVersionId,
        status: "open",
        baseNetworkRevision: 1,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: { assetCode: "P-001" },
            },
          ],
        },
        associations: [
          {
            id: "assoc-1",
            fromFeatureId: "feature-1",
            toFeatureId: "feature-2",
            associationType: "connected_to",
            version: 1,
          },
        ],
      },
    },
  };
}
```

- [ ] **Step 2: Add failing test for successful open flow**

Append this test inside `describe("work orders store", () => { ... })`:

```ts
it("opens selected work order and stores workspace", async () => {
  openEditVersionMock.mockResolvedValue(openEditVersionResponse());
  fetchWorkspaceMock.mockResolvedValue(workspaceResponse());

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
  store.selectWorkOrder("wo-1");

  await store.openSelectedWorkOrder();

  expect(openEditVersionMock).toHaveBeenCalledWith("wo-1");
  expect(fetchWorkspaceMock).toHaveBeenCalledWith("wo-1", "ev-1");
  expect(store.items[0].status).toBe("in_progress");
  expect(store.openedWorkOrderId).toBe("wo-1");
  expect(store.openedEditVersionId).toBe("ev-1");
  expect(store.activeWorkspace?.workOrder.code).toBe("WO-001");
  expect(store.activeWorkspaceKey).toBe("wo-1:ev-1");
  expect(store.selectedOpenWorkspaceError).toBeNull();
  expect(store.isOpeningWorkspace).toBe(false);
});
```

- [ ] **Step 3: Add failing test for failed workspace load after successful POST**

```ts
it("keeps action retry available when workspace loading fails after open", async () => {
  openEditVersionMock.mockResolvedValue(openEditVersionResponse());
  fetchWorkspaceMock.mockRejectedValue(new Error("workspace failed"));

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
  store.selectWorkOrder("wo-1");

  await store.openSelectedWorkOrder();

  expect(store.items[0].status).toBe("in_progress");
  expect(store.workspace).toBeNull();
  expect(store.openedWorkOrderId).toBeNull();
  expect(store.selectedOpenWorkspaceError).toBe(
    "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
  );
  expect(store.isOpeningWorkspace).toBe(false);
});
```

- [ ] **Step 4: Add failing test for stale response guard**

```ts
it("does not replace workspace when selection changed during opening", async () => {
  openEditVersionMock.mockResolvedValue(openEditVersionResponse("wo-1"));
  fetchWorkspaceMock.mockResolvedValue(workspaceResponse("wo-1", "ev-1"));

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
    {
      id: "wo-2",
      code: "WO-002",
      title: "Проверка второго участка",
      description: null,
      status: "assigned",
    },
  ];
  store.selectWorkOrder("wo-1");

  const opening = store.openSelectedWorkOrder();
  store.selectWorkOrder("wo-2");
  await opening;

  expect(store.selectedWorkOrderId).toBe("wo-2");
  expect(store.openedWorkOrderId).toBeNull();
  expect(store.activeWorkspace).toBeNull();
  expect(store.openWorkspaceErrorByWorkOrderId["wo-1"]).toBeUndefined();
});
```

- [ ] **Step 5: Run store tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts
```

Expected: FAIL because `openSelectedWorkOrder`, `openedWorkOrderId`,
`openedEditVersionId`, `activeWorkspace`, `activeWorkspaceKey`,
`selectedOpenWorkspaceError`, and new API exports do not exist yet.

- [ ] **Step 6: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record the failing test output in the task notes.

## Task 2: Contracts, API Wrappers, And Store Implementation

**Files:**
- Modify: `apps/frontend/src/contracts/work-orders.ts`
- Modify: `apps/frontend/src/api/workOrders.ts`
- Modify: `apps/frontend/src/stores/workOrders.ts`
- Test: `apps/frontend/src/stores/workOrders.test.ts`

- [ ] **Step 1: Extend frontend contracts**

Append these imports and types to `apps/frontend/src/contracts/work-orders.ts`:

```ts
import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from "geojson";

export type EditVersionStatus = "open";

export type EditVersionSummary = {
  id: string;
  workOrderId: string;
  ownerId: string;
  status: EditVersionStatus;
  baseNetworkRevision: number;
  createdAt: string;
  lastOpenedAt: string;
};

export type OpenEditVersionResponse = {
  created: boolean;
  editVersion: EditVersionSummary;
};

export type WorkspaceAoi = {
  id: string;
  name: string;
  description: string | null;
  geometry: Polygon | MultiPolygon;
  extent: [number, number, number, number];
};

export type WorkspaceFeature = Feature<Geometry, Record<string, unknown>> & {
  id: string;
};

export type WorkspaceFeatureCollection = Omit<
  FeatureCollection<Geometry, Record<string, unknown>>,
  "features"
> & {
  features: WorkspaceFeature[];
};

export type WorkspaceAssociation = {
  id: string;
  fromFeatureId: string;
  toFeatureId: string;
  associationType: string;
  version: number;
};

export type WorkspaceResponse = {
  workOrder: {
    id: string;
    code: string;
    title: string;
    description: string | null;
    status: WorkOrderStatus;
    scope: {
      aoi: WorkspaceAoi;
    };
    editVersion: {
      id: string;
      status: EditVersionStatus;
      baseNetworkRevision: number;
      features: WorkspaceFeatureCollection;
      associations: WorkspaceAssociation[];
    };
  };
};
```

If TypeScript complains that imports must be first, move the new import to the
top of the file above `export type WorkOrderStatus`.

- [ ] **Step 2: Add API wrapper methods**

Update `apps/frontend/src/api/workOrders.ts` to:

```ts
import { http } from "@/api/http";
import type {
  AssignedWorkOrdersResponse,
  OpenEditVersionResponse,
  WorkspaceResponse,
} from "@/contracts/work-orders";

export async function fetchAssignedWorkOrders() {
  const response = await http.get<AssignedWorkOrdersResponse>(
    "/api/v1/work-orders/assigned-to-me",
  );
  return response.data;
}

export async function openEditVersion(
  workOrderId: string,
): Promise<OpenEditVersionResponse> {
  const response = await http.post<OpenEditVersionResponse>(
    `/api/v1/work-orders/${workOrderId}/edit-versions`,
  );
  return response.data;
}

export async function fetchWorkspace(
  workOrderId: string,
  editVersionId: string,
): Promise<WorkspaceResponse> {
  const response = await http.get<WorkspaceResponse>(
    `/api/v1/work-orders/${workOrderId}/edit-versions/${editVersionId}/workspace`,
  );
  return response.data;
}
```

- [ ] **Step 3: Extend store state and getters**

Modify `apps/frontend/src/stores/workOrders.ts` imports:

```ts
import {
  fetchAssignedWorkOrders,
  fetchWorkspace,
  openEditVersion,
} from "@/api/workOrders";
import type {
  WorkOrderStatus,
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";
```

Extend `WorkOrdersState`:

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
  openWorkspaceRequestSeq: number;
};
```

Extend initial state:

```ts
openedWorkOrderId: null,
openedEditVersionId: null,
workspace: null,
isOpeningWorkspace: false,
openWorkspaceErrorByWorkOrderId: {},
lastFittedWorkspaceKey: null,
openWorkspaceRequestSeq: 0,
```

Replace the getters block with:

```ts
getters: {
  selectedWorkOrder: (state) =>
    state.items.find((item) => item.id === state.selectedWorkOrderId) ?? null,
  activeWorkspace: (state) => {
    if (
      !state.workspace ||
      state.selectedWorkOrderId === null ||
      state.openedWorkOrderId !== state.selectedWorkOrderId
    ) {
      return null;
    }
    return state.workspace;
  },
  activeWorkspaceKey: (state) => {
    if (
      state.selectedWorkOrderId === null ||
      state.openedWorkOrderId !== state.selectedWorkOrderId ||
      state.openedEditVersionId === null
    ) {
      return null;
    }
    return `${state.openedWorkOrderId}:${state.openedEditVersionId}`;
  },
  selectedOpenWorkspaceError: (state) => {
    if (!state.selectedWorkOrderId) {
      return null;
    }
    return state.openWorkspaceErrorByWorkOrderId[state.selectedWorkOrderId] ?? null;
  },
},
```

- [ ] **Step 4: Implement workspace actions**

Add these actions inside the existing `actions` block:

```ts
async openSelectedWorkOrder() {
  const workOrderId = this.selectedWorkOrderId;
  if (!workOrderId || this.isOpeningWorkspace) {
    return;
  }

  const requestSeq = this.openWorkspaceRequestSeq + 1;
  this.openWorkspaceRequestSeq = requestSeq;
  this.isOpeningWorkspace = true;
  this.openWorkspaceErrorByWorkOrderId = {
    ...this.openWorkspaceErrorByWorkOrderId,
    [workOrderId]: undefined,
  };

  try {
    const openResult = await openEditVersion(workOrderId);
    this.updateWorkOrderStatus(workOrderId, "in_progress");

    const editVersionId = openResult.editVersion.id;
    const workspace = await fetchWorkspace(workOrderId, editVersionId);

    if (
      this.openWorkspaceRequestSeq !== requestSeq ||
      this.selectedWorkOrderId !== workOrderId
    ) {
      return;
    }

    this.openedWorkOrderId = workOrderId;
    this.openedEditVersionId = editVersionId;
    this.workspace = workspace;
  } catch {
    if (
      this.openWorkspaceRequestSeq === requestSeq &&
      this.selectedWorkOrderId === workOrderId
    ) {
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
        [workOrderId]:
          "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
      };
    }
  } finally {
    if (this.openWorkspaceRequestSeq === requestSeq) {
      this.isOpeningWorkspace = false;
    }
  }
},
isWorkOrderOpened(workOrderId: string): boolean {
  return (
    this.openedWorkOrderId === workOrderId &&
    this.workspace !== null &&
    this.openedEditVersionId !== null
  );
},
markWorkspaceFitted(workspaceKey: string): void {
  this.lastFittedWorkspaceKey = workspaceKey;
},
shouldFitWorkspace(workspaceKey: string | null): boolean {
  return workspaceKey !== null && this.lastFittedWorkspaceKey !== workspaceKey;
},
updateWorkOrderStatus(workOrderId: string, status: WorkOrderStatus): void {
  this.items = this.items.map((item) =>
    item.id === workOrderId ? { ...item, status } : item,
  );
},
clearOpenedWorkspace(): void {
  this.openedWorkOrderId = null;
  this.openedEditVersionId = null;
  this.workspace = null;
  this.lastFittedWorkspaceKey = null;
},
```

Keep existing `selectWorkOrder()` and `clearSelection()` actions, but update
`clearSelection()` to also clear the visible workspace:

```ts
clearSelection() {
  this.selectedWorkOrderId = null;
  this.clearOpenedWorkspace();
},
```

- [ ] **Step 5: Preserve or clear opened workspace when reloading list**

Inside `loadAssigned()`, after `this.items = result.workOrders;`, keep the
existing selected-id cleanup and add:

```ts
if (
  this.openedWorkOrderId &&
  !this.items.some((item) => item.id === this.openedWorkOrderId)
) {
  this.clearOpenedWorkspace();
}
```

If the selected work order disappears, clear both selection and workspace:

```ts
if (
  this.selectedWorkOrderId &&
  !this.items.some((item) => item.id === this.selectedWorkOrderId)
) {
  this.selectedWorkOrderId = null;
  this.clearOpenedWorkspace();
}
```

- [ ] **Step 6: Run store tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts
```

Expected: PASS.

- [ ] **Step 7: Run typecheck for contract naming**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS. If it fails on property names, align frontend names with the
existing backend JSON: `editVersion`, `baseNetworkRevision`, `ownerId`,
`fromFeatureId`, `toFeatureId`, `associationType`.

- [ ] **Step 8: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record the passing store test command in the task notes.

## Task 3: Editor Work Orders View Tests

**Files:**
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
- Later modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`

- [ ] **Step 1: Extend the MapView mock**

Replace the existing `MapView` mock with:

```ts
vi.mock("@/components/MapView.vue", () => ({
  default: {
    name: "MapView",
    props: ["mode", "workspace", "workspaceKey", "shouldFitWorkspace"],
    emits: ["workspaceFitted"],
    template:
      '<div data-test="map-view" :data-mode="mode" :data-workspace-key="workspaceKey"></div>',
  },
}));
```

Add helpers below `const loadAssignedMock = vi.fn();`:

```ts
const openSelectedWorkOrderMock = vi.fn();

function assignedWorkOrder() {
  return {
    id: "wo-1",
    code: "WO-001",
    title: "Проверка участка фидера",
    description: null,
    status: "assigned" as const,
  };
}

function inProgressWorkOrder() {
  return {
    ...assignedWorkOrder(),
    status: "in_progress" as const,
  };
}
```

- [ ] **Step 2: Add failing test for `Начать` visibility**

```ts
it("shows start action only for selected assigned work order", async () => {
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
  store.openSelectedWorkOrder = openSelectedWorkOrderMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.get('[data-test="open-work-order-wo-1"]').text()).toBe(
    "Начать",
  );
  expect(wrapper.find('[data-test="open-work-order-wo-2"]').exists()).toBe(
    false,
  );

  await wrapper.get('[data-test="open-work-order-wo-1"]').trigger("click");
  expect(openSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 3: Add failing test for `Продолжить` visibility**

```ts
it("shows continue action for selected in-progress work order", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [inProgressWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.loadAssigned = loadAssignedMock;
  store.openSelectedWorkOrder = openSelectedWorkOrderMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.get('[data-test="open-work-order-wo-1"]').text()).toBe(
    "Продолжить",
  );
});
```

- [ ] **Step 4: Add failing test for hidden action and workspace map after open**

```ts
it("hides action and renders workspace map for opened selected work order", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [inProgressWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: "ev-1",
        status: "open",
        baseNetworkRevision: 1,
        features: { type: "FeatureCollection", features: [] },
        associations: [],
      },
    },
  };
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.find('[data-test="open-work-order-wo-1"]').exists()).toBe(
    false,
  );
  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "workspace",
  );
  expect(wrapper.get('[data-test="map-view"]').attributes("data-workspace-key")).toBe(
    "wo-1:ev-1",
  );
});
```

- [ ] **Step 5: Add failing test for selected-row error**

```ts
it("shows open error near selected work order", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [assignedWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.openWorkspaceErrorByWorkOrderId = {
    "wo-1": "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
  };
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.get('[data-test="open-work-order-error-wo-1"]').text()).toContain(
    "Не удалось открыть рабочую версию",
  );
});
```

- [ ] **Step 6: Run component tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: FAIL because the component does not render open actions, errors, or
workspace map props yet.

- [ ] **Step 7: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record the failing test output in the task notes.

## Task 4: Editor Work Orders View Implementation

**Files:**
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`
- Test: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`

- [ ] **Step 1: Add script helpers**

In `apps/frontend/src/components/EditorWorkOrdersView.vue`, add these helpers
inside `<script setup lang="ts">`:

```ts
function actionLabel(status: string): string {
  if (status === "in_progress") {
    return "Продолжить";
  }
  return "Начать";
}

function canShowOpenAction(workOrderId: string): boolean {
  return (
    workOrders.selectedWorkOrderId === workOrderId &&
    !workOrders.isWorkOrderOpened(workOrderId)
  );
}

function openError(workOrderId: string): string | null {
  return workOrders.openWorkspaceErrorByWorkOrderId[workOrderId] ?? null;
}
```

- [ ] **Step 2: Update work order item template without nested buttons**

Replace the current `<li>` body in `EditorWorkOrdersView.vue` with this
structure. The action button must be a sibling of the selection button, not a
button nested inside another button:

```vue
<div
  class="workOrderCard"
  :class="{
    isSelected: workOrders.selectedWorkOrderId === workOrder.id,
  }"
>
  <button
    class="workOrderButton"
    type="button"
    :data-test="`work-order-${workOrder.id}`"
    @click="workOrders.selectWorkOrder(workOrder.id)"
  >
    <span class="workOrderCode">{{ workOrder.code }}</span>
    <span class="workOrderTitle">{{ workOrder.title }}</span>
    <span class="workOrderStatus">{{ statusLabel(workOrder.status) }}</span>
    <span v-if="workOrder.description" class="workOrderDescription">
      {{ workOrder.description }}
    </span>
  </button>

  <div
    v-if="openError(workOrder.id)"
    class="workOrderError"
    :data-test="`open-work-order-error-${workOrder.id}`"
  >
    {{ openError(workOrder.id) }}
  </div>

  <div v-if="canShowOpenAction(workOrder.id)" class="workOrderActionRow">
    <button
      class="openWorkspaceButton"
      type="button"
      :data-test="`open-work-order-${workOrder.id}`"
      :disabled="workOrders.isOpeningWorkspace"
      @click="workOrders.openSelectedWorkOrder"
    >
      {{
        workOrders.isOpeningWorkspace
          ? "Открываем..."
          : actionLabel(workOrder.status)
      }}
    </button>
  </div>
</div>
```

This moves the selected visual state from `.workOrderButton` to `.workOrderCard`.

- [ ] **Step 3: Switch map pane between empty and workspace modes**

Replace:

```vue
<MapView mode="empty" />
```

with:

```vue
<MapView
  v-if="workOrders.activeWorkspace"
  mode="workspace"
  :workspace="workOrders.activeWorkspace"
  :workspace-key="workOrders.activeWorkspaceKey"
  :should-fit-workspace="workOrders.shouldFitWorkspace(workOrders.activeWorkspaceKey)"
  @workspace-fitted="workOrders.markWorkspaceFitted"
/>
<MapView v-else mode="empty" />
```

- [ ] **Step 4: Update card styles**

Replace the `.workOrderButton` and `.workOrderButton.isSelected` rules with:

```css
.workOrderCard {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.workOrderCard.isSelected {
  border-color: #166534;
  box-shadow: inset 3px 0 0 #166534;
}

.workOrderButton {
  width: 100%;
  display: grid;
  gap: 5px;
  padding: 0;
  text-align: left;
  border: 0;
  background: transparent;
  font: inherit;
  cursor: pointer;
}
```

Append:

```css
.workOrderError {
  color: #b91c1c;
  font-size: 13px;
  line-height: 1.35;
}

.workOrderActionRow {
  display: flex;
  justify-content: flex-start;
}

.openWorkspaceButton {
  border: 1px solid #166534;
  border-radius: 8px;
  padding: 7px 10px;
  background: #166534;
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.openWorkspaceButton:disabled {
  opacity: 0.7;
  cursor: wait;
}
```

- [ ] **Step 5: Run component tests**

Run:

```powershell
cd apps/frontend
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS. If the existing local-selection test expects the `isSelected`
class on `[data-test="work-order-wo-1"]`, update the assertion to check the
closest `.workOrderCard`:

```ts
expect(wrapper.get('[data-test="work-order-wo-1"]').element.closest(".workOrderCard")?.classList.contains("isSelected")).toBe(true);
```

- [ ] **Step 6: Run store and component tests together**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record the passing commands in the task notes.

## Task 5: Workspace Map Layer Helper

**Files:**
- Create: `apps/frontend/src/map/workspace-layers.ts`
- Create: `apps/frontend/src/map/workspace-layers.test.ts`

- [ ] **Step 1: Write failing helper tests**

Create `apps/frontend/src/map/workspace-layers.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ensureWorkspaceLayers,
  fitWorkspaceToAoi,
  setWorkspaceData,
} from "@/map/workspace-layers";
import type { WorkspaceResponse } from "@/contracts/work-orders";

const setDataMock = vi.fn();

function workspace(): WorkspaceResponse {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: "ev-1",
        status: "open",
        baseNetworkRevision: 1,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: { assetCode: "P-001" },
            },
          ],
        },
        associations: [],
      },
    },
  };
}

function fakeMap() {
  const sources = new Map<string, unknown>();
  const layers = new Set<string>();
  return {
    addSource: vi.fn((id: string, source: unknown) => {
      sources.set(id, { ...source, setData: setDataMock });
    }),
    getSource: vi.fn((id: string) => sources.get(id)),
    addLayer: vi.fn((layer: { id: string }) => {
      layers.add(layer.id);
    }),
    getLayer: vi.fn((id: string) => (layers.has(id) ? { id } : undefined)),
    fitBounds: vi.fn(),
  };
}

describe("workspace map layers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates read-only workspace sources and layers", () => {
    const map = fakeMap();

    ensureWorkspaceLayers(map as never);

    expect(map.addSource).toHaveBeenCalledWith(
      "workspace:aoi",
      expect.objectContaining({ type: "geojson" }),
    );
    expect(map.addSource).toHaveBeenCalledWith(
      "workspace:features",
      expect.objectContaining({ type: "geojson" }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: "workspace:aoi:fill" }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: "workspace:features:points" }),
    );
  });

  it("sets AOI and feature data", () => {
    const map = fakeMap();
    ensureWorkspaceLayers(map as never);

    setWorkspaceData(map as never, workspace());

    expect(setDataMock).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "FeatureCollection",
        features: expect.any(Array),
      }),
    );
    expect(setDataMock).toHaveBeenCalledTimes(2);
  });

  it("fits map to AOI extent", () => {
    const map = fakeMap();

    fitWorkspaceToAoi(map as never, workspace());

    expect(map.fitBounds).toHaveBeenCalledWith(
      [
        [65.5, 44.8],
        [65.54, 44.84],
      ],
      { padding: 48, duration: 0 },
    );
  });
});
```

- [ ] **Step 2: Run helper tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/map/workspace-layers.test.ts
```

Expected: FAIL because `workspace-layers.ts` does not exist.

- [ ] **Step 3: Implement workspace map helper**

Create `apps/frontend/src/map/workspace-layers.ts`:

```ts
import type { GeoJSONSource, Map } from "maplibre-gl";
import type { FeatureCollection, Geometry } from "geojson";
import type { WorkspaceResponse } from "@/contracts/work-orders";

const emptyFeatureCollection: FeatureCollection<Geometry, Record<string, unknown>> =
  {
    type: "FeatureCollection",
    features: [],
  };

const aoiSourceId = "workspace:aoi";
const featureSourceId = "workspace:features";

export function ensureWorkspaceLayers(map: Map | null): void {
  if (!map) {
    return;
  }

  if (!map.getSource(aoiSourceId)) {
    map.addSource(aoiSourceId, {
      type: "geojson",
      data: emptyFeatureCollection,
    });
  }

  if (!map.getSource(featureSourceId)) {
    map.addSource(featureSourceId, {
      type: "geojson",
      data: emptyFeatureCollection,
    });
  }

  addLayerIfMissing(map, {
    id: "workspace:aoi:fill",
    type: "fill",
    source: aoiSourceId,
    paint: {
      "fill-color": "#f59e0b",
      "fill-opacity": 0.14,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:aoi:outline",
    type: "line",
    source: aoiSourceId,
    paint: {
      "line-color": "#d97706",
      "line-width": 2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:polygons",
    type: "fill",
    source: featureSourceId,
    filter: ["match", ["geometry-type"], ["Polygon", "MultiPolygon"], true, false],
    paint: {
      "fill-color": "#2563eb",
      "fill-opacity": 0.2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:polygon-outline",
    type: "line",
    source: featureSourceId,
    filter: ["match", ["geometry-type"], ["Polygon", "MultiPolygon"], true, false],
    paint: {
      "line-color": "#1d4ed8",
      "line-width": 2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:lines",
    type: "line",
    source: featureSourceId,
    filter: ["match", ["geometry-type"], ["LineString", "MultiLineString"], true, false],
    paint: {
      "line-color": "#0f766e",
      "line-width": 3,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:points",
    type: "circle",
    source: featureSourceId,
    filter: ["match", ["geometry-type"], ["Point", "MultiPoint"], true, false],
    paint: {
      "circle-color": "#7c3aed",
      "circle-radius": 5,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1,
    },
  });
}

export function setWorkspaceData(
  map: Map | null,
  workspace: WorkspaceResponse,
): void {
  if (!map) {
    return;
  }

  const aoiSource = map.getSource(aoiSourceId) as GeoJSONSource | undefined;
  const featureSource = map.getSource(featureSourceId) as
    | GeoJSONSource
    | undefined;

  aoiSource?.setData({
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: workspace.workOrder.scope.aoi.geometry,
        properties: {
          id: workspace.workOrder.scope.aoi.id,
          name: workspace.workOrder.scope.aoi.name,
        },
      },
    ],
  });
  featureSource?.setData(workspace.workOrder.editVersion.features);
}

export function fitWorkspaceToAoi(
  map: Map | null,
  workspace: WorkspaceResponse,
): void {
  if (!map) {
    return;
  }

  const [west, south, east, north] = workspace.workOrder.scope.aoi.extent;
  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    { padding: 48, duration: 0 },
  );
}

function addLayerIfMissing(
  map: Map,
  layer: Parameters<Map["addLayer"]>[0],
): void {
  if (!map.getLayer(layer.id)) {
    map.addLayer(layer);
  }
}
```

- [ ] **Step 4: Run helper tests**

Run:

```powershell
cd apps/frontend
npm test -- src/map/workspace-layers.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run typecheck**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS. If MapLibre expression types are too narrow, type the layer
objects with `Parameters<Map["addLayer"]>[0]` before passing them to
`addLayerIfMissing`.

- [ ] **Step 6: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record helper test and typecheck results in the task notes.

## Task 6: MapView Workspace Mode

**Files:**
- Modify: `apps/frontend/src/components/MapView.test.ts`
- Modify: `apps/frontend/src/components/MapView.vue`
- Uses: `apps/frontend/src/map/workspace-layers.ts`

- [ ] **Step 1: Mock workspace helper in MapView tests**

Add these mocks to the `mocks` object in `apps/frontend/src/components/MapView.test.ts`:

```ts
ensureWorkspaceLayers: vi.fn(),
fitWorkspaceToAoi: vi.fn(),
setWorkspaceData: vi.fn(),
```

Add this module mock near the other `vi.mock(...)` calls:

```ts
vi.mock("@/map/workspace-layers", () => ({
  ensureWorkspaceLayers: mocks.ensureWorkspaceLayers,
  fitWorkspaceToAoi: mocks.fitWorkspaceToAoi,
  setWorkspaceData: mocks.setWorkspaceData,
}));
```

Add helper:

```ts
function workspace() {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: "ev-1",
        status: "open",
        baseNetworkRevision: 1,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: { assetCode: "P-001" },
            },
          ],
        },
        associations: [
          {
            id: "assoc-1",
            fromFeatureId: "feature-1",
            toFeatureId: "feature-2",
            associationType: "connected_to",
            version: 1,
          },
        ],
      },
    },
  };
}
```

- [ ] **Step 2: Add failing workspace mode test**

Append:

```ts
it("renders read-only workspace mode without legacy layer loading", async () => {
  const { default: MapView } = await import("@/components/MapView.vue");

  const wrapper = mount(MapView, {
    props: {
      mode: "workspace",
      workspace: workspace(),
      workspaceKey: "wo-1:ev-1",
      shouldFitWorkspace: true,
    },
  });
  await flushPromises();

  expect(mocks.createMap).toHaveBeenCalledTimes(1);
  expect(mocks.ensureWorkspaceLayers).toHaveBeenCalledTimes(1);
  expect(mocks.setWorkspaceData).toHaveBeenCalledWith(
    expect.anything(),
    workspace(),
  );
  expect(mocks.fitWorkspaceToAoi).toHaveBeenCalledWith(
    expect.anything(),
    workspace(),
  );
  expect(wrapper.emitted("workspaceFitted")?.[0]).toEqual(["wo-1:ev-1"]);
  expect(mocks.loadLayers).not.toHaveBeenCalled();
  expect(mocks.reloadFeatures).not.toHaveBeenCalled();
  expect(mocks.handleRealtimeLayerChange).not.toHaveBeenCalled();
  expect(mocks.enableEditingOverlaySync).not.toHaveBeenCalled();
  expect(wrapper.text()).toContain("WO-001");
  expect(wrapper.text()).toContain("features: 1");
  expect(wrapper.text()).toContain("associations: 1");
});
```

- [ ] **Step 3: Run MapView tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/components/MapView.test.ts
```

Expected: FAIL because `MapView` does not accept workspace props or call
workspace helper yet.

- [ ] **Step 4: Implement props, emits, and workspace branch**

In `apps/frontend/src/components/MapView.vue`, add imports:

```ts
import { watch } from "vue";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import {
  ensureWorkspaceLayers,
  fitWorkspaceToAoi,
  setWorkspaceData,
} from "@/map/workspace-layers";
```

If `computed, onBeforeUnmount, onMounted, ref` are already imported from
`vue`, change that import to:

```ts
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
```

Extend props:

```ts
defineProps<{
  mode?: "empty" | "editing" | "workspace";
  workspace?: WorkspaceResponse | null;
  workspaceKey?: string | null;
  shouldFitWorkspace?: boolean;
}>()
```

With defaults:

```ts
const props = withDefaults(
  defineProps<{
    mode?: "empty" | "editing" | "workspace";
    workspace?: WorkspaceResponse | null;
    workspaceKey?: string | null;
    shouldFitWorkspace?: boolean;
  }>(),
  {
    mode: "editing",
    workspace: null,
    workspaceKey: null,
    shouldFitWorkspace: false,
  },
);
```

Add emits:

```ts
const emit = defineEmits<{
  workspaceFitted: [workspaceKey: string];
}>();
```

Add helper function before `onMounted`:

```ts
function renderWorkspace(): void {
  if (!map.value || !props.workspace) {
    labelText.value = "Workspace не выбран";
    return;
  }

  ensureWorkspaceLayers(map.value);
  setWorkspaceData(map.value, props.workspace);

  const editVersion = props.workspace.workOrder.editVersion;
  labelText.value = `${props.workspace.workOrder.code} | EditVersion: ${editVersion.status} | baseNetworkRevision: ${editVersion.baseNetworkRevision} | features: ${editVersion.features.features.length} | associations: ${editVersion.associations.length}`;

  if (props.shouldFitWorkspace && props.workspaceKey) {
    fitWorkspaceToAoi(map.value, props.workspace);
    emit("workspaceFitted", props.workspaceKey);
  }
}
```

In `onMounted`, after `createMap()` succeeds and before the empty-mode branch,
add:

```ts
if (props.mode === "workspace") {
  renderWorkspace();
  return;
}
```

Add watcher after `onMounted`:

```ts
watch(
  () => [props.mode, props.workspace, props.shouldFitWorkspace] as const,
  () => {
    if (props.mode === "workspace") {
      renderWorkspace();
    }
  },
);
```

- [ ] **Step 5: Ensure template status badge remains valid**

No template rewrite is required because existing `<div class="badge">{{ labelText }}</div>`
will display workspace status. Confirm `realtimeBadge` remains guarded by
`props.mode === 'editing'`.

- [ ] **Step 6: Run MapView tests**

Run:

```powershell
cd apps/frontend
npm test -- src/components/MapView.test.ts
```

Expected: PASS.

- [ ] **Step 7: Run focused frontend tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts src/map/workspace-layers.test.ts src/components/MapView.test.ts
```

Expected: PASS.

- [ ] **Step 8: Checkpoint**

Do not run `git add` or `git commit` unless the user explicitly asks for Git
operations. Record focused frontend test results in the task notes.

## Task 7: Documentation, Registry, And Final Verification

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`
- Modify: `docs/agent-memory/file-map.md`
- Test: frontend verification commands

- [ ] **Step 1: Add implementation plan link to sprint README**

In `docs/release_1/sprint_1/README.md`, after the design link for Интенсив 12,
add:

```markdown
- [План реализации Edit Workspace Интенсива 12](2026-06-25-sprint-1-day-12-edit-workspace-implementation-plan.md)
```

- [ ] **Step 2: Add compact file-map entry**

In `docs/agent-memory/file-map.md`, near the Sprint 1 entries, add:

```markdown
- GeoService Sprint 1 Day 12 Edit Workspace frontend: `docs/release_1/sprint_1/2026-06-25-sprint-1-day-12-edit-workspace-design.md`, `docs/release_1/sprint_1/2026-06-25-sprint-1-day-12-edit-workspace-implementation-plan.md`, `apps/frontend/src/components/EditorWorkOrdersView.vue`, `apps/frontend/src/components/MapView.vue`, `apps/frontend/src/stores/workOrders.ts`, `apps/frontend/src/api/workOrders.ts`, `apps/frontend/src/contracts/work-orders.ts`
```

- [ ] **Step 3: Run frontend focused tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts src/map/workspace-layers.test.ts src/components/MapView.test.ts
```

Expected: PASS.

- [ ] **Step 4: Run frontend typecheck**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS.

- [ ] **Step 5: Run frontend build**

Run:

```powershell
cd apps/frontend
npm run build
```

Expected: PASS with successful `vue-tsc -b` and Vite build.

- [ ] **Step 6: Run memory-needed check because file-map changed**

Run from repository root:

```powershell
python scripts/check-memory-needed.py --check
```

Expected: PASS or a warning that does not require a new durable memory entry.
Do not create a new memory entry for task completion, changed files, test logs
or plan completion.

- [ ] **Step 7: Decide on repository-change ingest**

Do not run `/ingest repository-change` automatically. Run it only if the final
implementation introduces new durable technical knowledge not already captured
by code, this plan, sprint README or Code_wiki. A likely outcome for this task
is: no repository-change ingest needed, because the implementation follows the
existing Workspace API and frontend architecture patterns.

- [ ] **Step 8: Final git status review**

Run:

```powershell
git status --short
```

Expected: implementation files and docs changed, with pre-existing `.obsidian/*`
changes still untouched. Do not stage or commit unless the user explicitly asks
for Git operations.

## Self-Review Notes

- Spec coverage: plan covers explicit `Начать` / `Продолжить`, selected-only
  action, hidden action after open, `POST -> GET` flow, local status update,
  selected-row error, stale response guard, read-only workspace map, AOI/features
  rendering, version status counts, first fit-to-AOI and frontend verification.
- Scope guard: no backend endpoints, migrations, editing API, realtime workspace
  events, association geometry rendering, review/post or audit changes are
  planned.
- Git rule: checkpoint steps intentionally avoid `git add` and `git commit`
  because repository memory requires explicit user approval for Git operations.
