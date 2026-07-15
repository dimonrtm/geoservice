# Workspace Details Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить длинный workspace badge на доступную responsive-панель над картой, которая до открытия показывает preview и primary action, а после открытия — устойчивый набор workspace metadata.

**Architecture:** Новый презентационный `WorkspaceDetailsPanel.vue` получает данные и UI state через props, эмитит `open` и предоставляет только `focusHeading()`. `EditorWorkOrdersView.vue` остаётся orchestration boundary между panel, Pinia store и `MapView`; store привязывает loading к `openingWorkOrderId`, а `MapView` перестаёт выводить metadata badge только в `workspace` mode.

**Tech Stack:** Vue 3 Composition API, TypeScript, Pinia 3, Vue Test Utils, Vitest, MapLibre GL, scoped CSS.

## Global Constraints

- Каноническая spec: `docs/superpowers/specs/2026-07-15-workspace-details-panel-design.md`.
- Не изменять backend endpoints, DTO, response JSON или frontend API contracts.
- До открытия использовать только `WorkOrderSummary`; не загружать AOI отдельным request.
- UI labels: `assigned -> Назначен`, `in_progress -> В работе`, `open -> Открыта`.
- Не показывать `workOrder.id`, `editVersion.id`, AOI extent, raw statuses или read-only пояснение.
- Primary action и open error должны находиться только в details panel, не в левой карточке.
- Длинный `.badge` удаляется только из `MapView mode="workspace"`; `empty`, `editing` и realtime statuses сохраняются.
- Explicit user open переводит focus на panel heading; restore при mount focus не меняет.
- Breakpoint остаётся `760px`; на mobile metadata образуют две колонки, AOI занимает всю ширину.
- Следовать TDD: сначала наблюдать ожидаемый FAIL, затем добавлять минимальную реализацию и повторять тест.
- Repository rule: не выполнять `git add`, `git commit` или `git push` и не запрашивать approval для них. Каждый task заканчивается unstaged review checkpoint вместо commit.

## File Structure

- Create: `apps/frontend/src/components/WorkspaceDetailsPanel.vue` — presentation, localization, semantic preview/details markup, action event и imperative focus boundary.
- Create: `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts` — изолированные component tests панели.
- Modify: `apps/frontend/src/stores/workOrders.ts` — заменить общий mutable loading boolean на `openingWorkOrderId` и derived busy getter.
- Modify: `apps/frontend/src/stores/workOrders.test.ts` — lifecycle и stale-request tests для identity-aware loading.
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue` — разместить panel над картой, перенести action/error, выполнить explicit-open focus и announcement.
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts` — integration tests preview/details, error, focus, restore и selection switching.
- Modify: `apps/frontend/src/components/MapView.vue` — не рендерить общий badge и не формировать metadata label в `workspace` mode.
- Modify: `apps/frontend/src/components/MapView.test.ts` — доказать отсутствие workspace badge и сохранение остальных badge modes.

---

### Task 1: Identity-Aware Workspace Opening State

**Files:**

- Modify: `apps/frontend/src/stores/workOrders.ts:14-27`
- Modify: `apps/frontend/src/stores/workOrders.ts:112-161`
- Modify: `apps/frontend/src/stores/workOrders.ts:223-331`
- Test: `apps/frontend/src/stores/workOrders.test.ts:134-174`
- Test: `apps/frontend/src/stores/workOrders.test.ts:238-409`
- Test: `apps/frontend/src/stores/workOrders.test.ts:441-473`

**Interfaces:**

- Consumes: существующие `selectedWorkOrderId`, `openWorkspaceRequestSeq`, `openSelectedWorkOrder()` и `restoreOpenedWorkspace()`.
- Produces: state `openingWorkOrderId: string | null` и getter `isOpeningWorkspace: boolean`.
- Produces for Task 3: точная проверка текущего loading — `workOrders.openingWorkOrderId === workOrders.selectedWorkOrder?.id`.

- [ ] **Step 1: Обновить reset expectation и добавить failing lifecycle test**

В test `resets user-scoped state and invalidates pending requests` заменить прямую запись boolean:

```ts
store.openingWorkOrderId = "wo-1";
```

И проверить оба публичных результата после `store.reset()`:

```ts
expect(store.openingWorkOrderId).toBeNull();
expect(store.isOpeningWorkspace).toBe(false);
```

После test `selects a work order locally without API calls` добавить:

```ts
it("tracks the initiating work order while open is pending", async () => {
  const openResponse = openEditVersionResponse("wo-1");
  const openDeferred = createDeferred<typeof openResponse>();
  openEditVersionMock.mockReturnValue(openDeferred.promise);
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

  expect(store.openingWorkOrderId).toBe("wo-1");
  expect(store.isOpeningWorkspace).toBe(true);

  store.selectWorkOrder("wo-2");
  expect(store.openingWorkOrderId).toBe("wo-1");

  openDeferred.resolve(openResponse);
  await opening;

  expect(fetchWorkspaceMock).not.toHaveBeenCalled();
  expect(store.openingWorkOrderId).toBeNull();
  expect(store.isOpeningWorkspace).toBe(false);
});
```

В success, restore, failed workspace и reset-during-open tests добавить финальную проверку:

```ts
expect(store.openingWorkOrderId).toBeNull();
```

- [ ] **Step 2: Запустить store test и подтвердить FAIL**

Run from `apps/frontend`:

```powershell
npm test -- src/stores/workOrders.test.ts
```

Expected: FAIL, потому что `openingWorkOrderId` отсутствует и pending request не содержит identity инициировавшего наряда.

- [ ] **Step 3: Заменить boolean state на opening work-order identity**

В `WorkOrdersState` заменить поле:

```ts
openingWorkOrderId: string | null;
```

В `createInitialWorkOrdersState()` использовать:

```ts
openingWorkOrderId: null,
```

В начало `getters` добавить derived busy state:

```ts
isOpeningWorkspace: (state) => state.openingWorkOrderId !== null,
```

В `openSelectedWorkOrder()` заменить guard и начало loading:

```ts
const workOrderId = this.selectedWorkOrderId;
if (!workOrderId || this.openingWorkOrderId !== null) {
  return;
}

const requestSeq = this.openWorkspaceRequestSeq + 1;
this.openWorkspaceRequestSeq = requestSeq;
this.openingWorkOrderId = workOrderId;
this.openWorkspaceErrorByWorkOrderId = {
  ...this.openWorkspaceErrorByWorkOrderId,
  [workOrderId]: undefined,
};
```

Его `finally` заменить identity-safe очисткой:

```ts
} finally {
  if (
    this.openWorkspaceRequestSeq === requestSeq &&
    this.openingWorkOrderId === workOrderId
  ) {
    this.openingWorkOrderId = null;
  }
}
```

В `restoreOpenedWorkspace()` заменить guard:

```ts
const storedWorkspace = readStoredOpenedWorkspace();
if (!storedWorkspace || this.openingWorkOrderId !== null) {
  return;
}
```

После создания `requestSeq` установить identity:

```ts
const requestSeq = this.openWorkspaceRequestSeq + 1;
this.openWorkspaceRequestSeq = requestSeq;
this.openingWorkOrderId = workOrderId;
this.selectedWorkOrderId = workOrderId;
```

Его `finally` заменить тем же guarded pattern:

```ts
} finally {
  if (
    this.openWorkspaceRequestSeq === requestSeq &&
    this.openingWorkOrderId === workOrderId
  ) {
    this.openingWorkOrderId = null;
  }
}
```

Удалить все mutable assignments `this.isOpeningWorkspace = ...`; getter остаётся совместимым read-only API для view и существующих assertions.

- [ ] **Step 4: Запустить store test и подтвердить PASS**

Run from `apps/frontend`:

```powershell
npm test -- src/stores/workOrders.test.ts
```

Expected: все tests файла PASS; success, error, restore, reset и selection-change завершаются с `openingWorkOrderId === null`.

- [ ] **Step 5: Проверить типы и unstaged diff Task 1**

```powershell
npm run typecheck
git -C ../.. diff --check
git -C ../.. diff -- apps/frontend/src/stores/workOrders.ts apps/frontend/src/stores/workOrders.test.ts
```

Expected: typecheck exit 0, `diff --check` без output, diff содержит только identity-aware loading и соответствующие tests. Не индексировать изменения.

---

### Task 2: Presentational Workspace Details Panel

**Files:**

- Create: `apps/frontend/src/components/WorkspaceDetailsPanel.vue`
- Create: `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts`
- Reference: `apps/frontend/src/contracts/work-orders.ts`

**Interfaces:**

- Consumes:

```ts
type WorkspaceDetailsPanelProps = {
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  errorMessage: string | null;
};
```

- Produces: event `open: []`.
- Produces: exposed method `focusHeading(): void`.
- Produces selectors for Task 3: `workspace-details-panel`, `workspace-details-title`, `workspace-open-action`, `workspace-open-error`, `workspace-details-grid`.

- [ ] **Step 1: Создать failing component tests**

Создать `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts`:

```ts
import { afterEach, describe, expect, it } from "vitest";
import { mount, type VueWrapper } from "@vue/test-utils";

import WorkspaceDetailsPanel from "@/components/WorkspaceDetailsPanel.vue";
import type {
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";

const mountedWrappers: VueWrapper[] = [];

type PanelTestProps = {
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  errorMessage: string | null;
};

function workOrder(
  overrides: Partial<WorkOrderSummary> = {},
): WorkOrderSummary {
  return {
    id: "wo-1",
    code: "WO-001",
    title: "Проверка участка фидера",
    description: "Проверить оборудование внутри области работ",
    status: "assigned",
    ...overrides,
  };
}

function workspace(): WorkspaceResponse {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: "Не показывать после открытия",
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
        id: "ev-secret-1",
        status: "open",
        baseNetworkRevision: 7,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: {},
            },
            {
              id: "feature-2",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.53, 44.83] },
              properties: {},
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

function mountPanel(
  props: Partial<PanelTestProps> = {},
) {
  const wrapper = mount(WorkspaceDetailsPanel, {
    props: {
      workOrder: workOrder(),
      workspace: null,
      isOpening: false,
      isOpenActionDisabled: false,
      errorMessage: null,
      ...props,
    },
    attachTo: document.body,
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

afterEach(() => {
  for (const wrapper of mountedWrappers.splice(0)) {
    wrapper.unmount();
  }
});

describe("WorkspaceDetailsPanel", () => {
  it("renders assigned preview and emits open", async () => {
    const wrapper = mountPanel();

    expect(wrapper.get('[data-test="workspace-code"]').text()).toBe("WO-001");
    expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
      "Проверка участка фидера",
    );
    expect(wrapper.get('[data-test="workspace-status"]').text()).toBe(
      "Назначен",
    );
    expect(wrapper.get('[data-test="workspace-description"]').text()).toContain(
      "Проверить оборудование",
    );
    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Начать",
    );

    await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
    expect(wrapper.emitted("open")).toHaveLength(1);
  });

  it("localizes in-progress preview and exposes loading semantics", () => {
    const wrapper = mountPanel({
      workOrder: workOrder({ status: "in_progress" }),
      isOpening: true,
      isOpenActionDisabled: true,
    });

    expect(wrapper.get('[data-test="workspace-status"]').text()).toBe(
      "В работе",
    );
    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Открываем…",
    );
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper.get('[data-test="workspace-details-panel"]').attributes("aria-busy"),
    ).toBe("true");
  });

  it("keeps the normal label while another work order is opening", () => {
    const wrapper = mountPanel({
      isOpening: false,
      isOpenActionDisabled: true,
    });

    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Начать",
    );
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper.get('[data-test="workspace-details-panel"]').attributes("aria-busy"),
    ).toBe("false");
  });

  it("renders an actionable alert in preview", () => {
    const wrapper = mountPanel({ errorMessage: "Не удалось открыть workspace" });

    const error = wrapper.get('[data-test="workspace-open-error"]');
    const action = wrapper.get('[data-test="workspace-open-action"]');
    expect(error.text()).toBe("Не удалось открыть workspace");
    expect(error.attributes("role")).toBe("alert");
    expect(action.attributes("aria-describedby")).toBe("workspace-open-error");
  });

  it("renders localized workspace details without technical values", () => {
    const wrapper = mountPanel({
      workOrder: workOrder({ status: "in_progress" }),
      workspace: workspace(),
    });

    expect(wrapper.get('[data-test="workspace-aoi"]').text()).toBe(
      "Рабочая область WO-001",
    );
    expect(wrapper.get('[data-test="workspace-version-status"]').text()).toBe(
      "Открыта",
    );
    expect(wrapper.get('[data-test="workspace-base-revision"]').text()).toBe(
      "7",
    );
    expect(wrapper.get('[data-test="workspace-feature-count"]').text()).toBe(
      "2",
    );
    expect(
      wrapper.get('[data-test="workspace-association-count"]').text(),
    ).toBe("1");
    expect(wrapper.find('[data-test="workspace-description"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(
      false,
    );
    expect(wrapper.text()).not.toContain("ev-secret-1");
    expect(wrapper.text()).not.toContain("in_progress");
    expect(wrapper.text()).not.toContain("open");
  });

  it("exposes focusHeading for the orchestration boundary", () => {
    const wrapper = mountPanel({ workspace: workspace() });
    const exposed = wrapper.vm as unknown as { focusHeading(): void };

    exposed.focusHeading();

    expect(document.activeElement).toBe(
      wrapper.get('[data-test="workspace-details-title"]').element,
    );
  });
});
```

- [ ] **Step 2: Запустить panel test и подтвердить FAIL**

```powershell
npm test -- src/components/WorkspaceDetailsPanel.test.ts
```

Expected: FAIL с module resolution error, потому что `WorkspaceDetailsPanel.vue` ещё не существует.

- [ ] **Step 3: Реализовать минимальный presentation component**

Создать `apps/frontend/src/components/WorkspaceDetailsPanel.vue`:

```vue
<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  EditVersionStatus,
  WorkOrderStatus,
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";

const props = defineProps<{
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  errorMessage: string | null;
}>();

const emit = defineEmits<{
  open: [];
}>();

const titleRef = ref<HTMLHeadingElement | null>(null);

const workOrderStatusText = computed(() =>
  workOrderStatusLabel(props.workOrder.status),
);
const actionText = computed(() => {
  if (props.isOpening) {
    return "Открываем…";
  }
  return props.workOrder.status === "in_progress" ? "Продолжить" : "Начать";
});

function workOrderStatusLabel(status: WorkOrderStatus): string {
  return status === "in_progress" ? "В работе" : "Назначен";
}

function editVersionStatusLabel(status: EditVersionStatus): string {
  return status === "open" ? "Открыта" : status;
}

function focusHeading(): void {
  titleRef.value?.focus();
}

defineExpose({ focusHeading });
</script>

<template>
  <section
    class="workspaceDetailsPanel"
    data-test="workspace-details-panel"
    aria-labelledby="workspace-details-title"
    :aria-busy="props.isOpening ? 'true' : 'false'"
  >
    <header class="detailsHeader">
      <div class="detailsIdentity">
        <div class="detailsContext">
          <span class="workOrderCode" data-test="workspace-code">
            {{ props.workOrder.code }}
          </span>
          <span class="statusBadge" data-test="workspace-status">
            {{ workOrderStatusText }}
          </span>
        </div>
        <h2
          id="workspace-details-title"
          ref="titleRef"
          data-test="workspace-details-title"
          tabindex="-1"
        >
          {{ props.workOrder.title }}
        </h2>
      </div>
    </header>

    <dl
      v-if="props.workspace"
      class="detailsGrid"
      data-test="workspace-details-grid"
    >
      <div class="detailItem isAoi">
        <dt>Область работ</dt>
        <dd data-test="workspace-aoi">
          {{ props.workspace.workOrder.scope.aoi.name }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Версия</dt>
        <dd data-test="workspace-version-status">
          {{ editVersionStatusLabel(props.workspace.workOrder.editVersion.status) }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Базовая ревизия</dt>
        <dd data-test="workspace-base-revision">
          {{ props.workspace.workOrder.editVersion.baseNetworkRevision }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Объекты</dt>
        <dd data-test="workspace-feature-count">
          {{ props.workspace.workOrder.editVersion.features.features.length }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Связи</dt>
        <dd data-test="workspace-association-count">
          {{ props.workspace.workOrder.editVersion.associations.length }}
        </dd>
      </div>
    </dl>

    <div v-else class="previewBody">
      <p
        v-if="props.workOrder.description"
        class="workOrderDescription"
        data-test="workspace-description"
      >
        {{ props.workOrder.description }}
      </p>

      <p
        v-if="props.errorMessage"
        id="workspace-open-error"
        class="openError"
        data-test="workspace-open-error"
        role="alert"
      >
        {{ props.errorMessage }}
      </p>

      <button
        class="openAction"
        type="button"
        data-test="workspace-open-action"
        :disabled="props.isOpenActionDisabled"
        :aria-describedby="
          props.errorMessage ? 'workspace-open-error' : undefined
        "
        @click="emit('open')"
      >
        {{ actionText }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.workspaceDetailsPanel {
  flex: 0 0 auto;
  min-width: 0;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  background: #fff;
  color: #0f172a;
}

.detailsHeader,
.detailsIdentity {
  min-width: 0;
}

.detailsContext {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
}

.workOrderCode {
  color: #166534;
  font-size: 12px;
  font-weight: 800;
}

.statusBadge {
  border-radius: 999px;
  padding: 2px 8px;
  background: #ecfdf5;
  color: #166534;
  font-size: 12px;
  font-weight: 700;
}

h2 {
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 18px;
  line-height: 1.3;
}

h2:focus-visible {
  outline: 3px solid rgba(22, 101, 52, 0.35);
  outline-offset: 4px;
}

.previewBody {
  display: grid;
  justify-items: start;
  gap: 10px;
  margin-top: 10px;
}

.workOrderDescription,
.openError {
  margin: 0;
  line-height: 1.4;
}

.workOrderDescription {
  color: #475569;
  font-size: 14px;
}

.openError {
  color: #b91c1c;
  font-size: 13px;
}

.openAction {
  min-width: 112px;
  border: 1px solid #166534;
  border-radius: 8px;
  padding: 8px 12px;
  background: #166534;
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.openAction:disabled {
  opacity: 0.7;
  cursor: wait;
}

.detailsGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 12px;
  margin: 12px 0 0;
}

.detailItem {
  min-width: 0;
}

.detailItem.isAoi {
  grid-column: span 2;
}

dt {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

@media (max-width: 760px) {
  .workspaceDetailsPanel {
    padding: 12px;
  }

  .detailsGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 12px;
  }

  .detailItem.isAoi {
    grid-column: 1 / -1;
  }
}
</style>
```

- [ ] **Step 4: Запустить panel test и подтвердить PASS**

```powershell
npm test -- src/components/WorkspaceDetailsPanel.test.ts
```

Expected: 6 tests PASS; preview/details, localization, loading, alert и exposed focus подтверждены.

- [ ] **Step 5: Проверить component quality и unstaged diff Task 2**

```powershell
npm run typecheck
npm run lint -- --no-warn-ignored src/components/WorkspaceDetailsPanel.vue src/components/WorkspaceDetailsPanel.test.ts
npx prettier --check src/components/WorkspaceDetailsPanel.vue src/components/WorkspaceDetailsPanel.test.ts
git -C ../.. diff --check
```

Expected: все команды exit 0. Если Prettier сообщает formatting differences, выполнить только:

```powershell
npx prettier --write src/components/WorkspaceDetailsPanel.vue src/components/WorkspaceDetailsPanel.test.ts
```

Затем повторить `prettier --check` и panel test. Оставить файлы unstaged.

---

### Task 3: Integrate Preview, Details, Error, Focus, and Responsive Layout

**Files:**

- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue:1-34`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue:92-159`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue:277-318`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts:1-333`
- Consume: `apps/frontend/src/components/WorkspaceDetailsPanel.vue`
- Consume: `apps/frontend/src/stores/workOrders.ts`

**Interfaces:**

- Consumes: `WorkspaceDetailsPanel` props/event/method from Task 2.
- Consumes: `openingWorkOrderId` и derived `isOpeningWorkspace` from Task 1.
- Produces: async handler `openSelectedWorkspace(): Promise<void>`.
- Produces: screen-reader announcement `Рабочее пространство <code> загружено` only after explicit action.
- Produces for Task 4: `MapView mode="workspace"` remains responsible only for map layers and fit.

- [ ] **Step 1: Добавить integration helpers и failing preview/details assertions**

В `EditorWorkOrdersView.test.ts` добавить import:

```ts
import type { WorkspaceResponse } from "@/contracts/work-orders";
```

После `inProgressWorkOrder()` добавить factory:

```ts
function workspaceResponse(): WorkspaceResponse {
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
        features: { type: "FeatureCollection", features: [] },
        associations: [],
      },
    },
  };
}
```

Заменить tests старого card action/error (`shows start action...`, `shows continue action...`, `hides action...`, `shows open error...`) следующими integration tests:

```ts
it("renders selected preview and opens from the right panel", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [
    { ...assignedWorkOrder(), description: "Описание выбранного наряда" },
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

  expect(wrapper.get('[data-test="workspace-details-panel"]').text()).toContain(
    "WO-001",
  );
  expect(wrapper.get('[data-test="workspace-description"]').text()).toContain(
    "Описание выбранного наряда",
  );
  expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
    "Начать",
  );
  expect(wrapper.find(".workOrderCard .openWorkspaceButton").exists()).toBe(
    false,
  );
  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "empty",
  );

  await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
  expect(openSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
});

it("renders continue for an in-progress preview", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [inProgressWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
    "Продолжить",
  );
});

it("renders details and workspace map for the opened selected work order", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [inProgressWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = workspaceResponse();
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(
    false,
  );
  expect(wrapper.get('[data-test="workspace-aoi"]').text()).toBe(
    "Рабочая область WO-001",
  );
  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "workspace",
  );
  expect(
    wrapper.get('[data-test="map-view"]').attributes("data-workspace-key"),
  ).toBe("wo-1:ev-1");
});

it("moves the selected open error into the right panel", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [assignedWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.openWorkspaceErrorByWorkOrderId = {
    "wo-1":
      "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
  };
  store.loadAssigned = loadAssignedMock;
  store.openSelectedWorkOrder = openSelectedWorkOrderMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  const error = wrapper.get('[data-test="workspace-open-error"]');
  expect(error.text()).toContain("Не удалось открыть рабочую версию");
  expect(error.attributes("role")).toBe("alert");
  expect(wrapper.find(".workOrderCard .workOrderError").exists()).toBe(false);

  await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
  expect(openSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
});

it("does not label a newly selected work order as opening", async () => {
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
  store.selectedWorkOrderId = "wo-2";
  store.openingWorkOrderId = "wo-1";
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  const action = wrapper.get('[data-test="workspace-open-action"]');
  expect(action.text()).toBe("Начать");
  expect(action.attributes("disabled")).toBeDefined();
});
```

- [ ] **Step 2: Добавить failing focus, restore и reselection tests**

Добавить в тот же describe:

```ts
it("focuses details and announces only after explicit open", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [assignedWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.loadAssigned = loadAssignedMock;
  store.openSelectedWorkOrder = vi.fn(async () => {
    store.updateWorkOrderStatus("wo-1", "in_progress");
    store.openedWorkOrderId = "wo-1";
    store.openedEditVersionId = "ev-1";
    store.workspace = workspaceResponse();
  });

  const host = document.createElement("div");
  document.body.append(host);
  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView, { attachTo: host });

  await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
  await flushPromises();

  expect(document.activeElement).toBe(
    wrapper.get('[data-test="workspace-details-title"]').element,
  );
  expect(wrapper.get('[data-test="workspace-announcement"]').text()).toBe(
    "Рабочее пространство WO-001 загружено",
  );

  wrapper.unmount();
  host.remove();
});

it("restores workspace without moving focus or announcing explicit success", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [inProgressWorkOrder()];
  store.loadAssigned = loadAssignedMock;
  store.restoreOpenedWorkspace = vi.fn(async () => {
    store.selectedWorkOrderId = "wo-1";
    store.openedWorkOrderId = "wo-1";
    store.openedEditVersionId = "ev-1";
    store.workspace = workspaceResponse();
  });

  const host = document.createElement("div");
  document.body.append(host);
  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView, { attachTo: host });
  await flushPromises();

  expect(document.activeElement).not.toBe(
    wrapper.get('[data-test="workspace-details-title"]').element,
  );
  expect(wrapper.get('[data-test="workspace-announcement"]').text()).toBe("");

  wrapper.unmount();
  host.remove();
});

it("returns to the saved workspace when its work order is selected again", async () => {
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
  store.selectedWorkOrderId = "wo-2";
  store.openedWorkOrderId = "wo-1";
  store.openedEditVersionId = "ev-1";
  store.workspace = workspaceResponse();
  store.loadAssigned = loadAssignedMock;
  store.openSelectedWorkOrder = openSelectedWorkOrderMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "empty",
  );
  expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
    "Второй наряд",
  );

  await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

  expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
    "workspace",
  );
  expect(wrapper.get('[data-test="workspace-aoi"]').text()).toBe(
    "Рабочая область WO-001",
  );
  expect(openSelectedWorkOrderMock).not.toHaveBeenCalled();
});
```

- [ ] **Step 3: Запустить EditorWorkOrdersView test и подтвердить FAIL**

```powershell
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: FAIL, потому что panel ещё не смонтирован в view, старые card action/error существуют, а explicit focus/announcement отсутствуют.

- [ ] **Step 4: Добавить orchestration handler и panel ref**

В `<script setup>` заменить import Vue и добавить panel import/type:

```ts
import { nextTick, onMounted, ref, watch } from "vue";

import MapView from "@/components/MapView.vue";
import WorkspaceDetailsPanel from "@/components/WorkspaceDetailsPanel.vue";
import { useWorkOrdersStore } from "@/stores/workOrders";

type WorkspaceDetailsPanelHandle = {
  focusHeading(): void;
};

const workOrders = useWorkOrdersStore();
const detailsPanelRef = ref<WorkspaceDetailsPanelHandle | null>(null);
const workspaceAnnouncement = ref("");

watch(
  () => workOrders.selectedWorkOrderId,
  () => {
    workspaceAnnouncement.value = "";
  },
);
```

Удалить functions `actionLabel`, `canShowOpenAction` и `openError`. Добавить:

```ts
async function openSelectedWorkspace(): Promise<void> {
  const workOrderId = workOrders.selectedWorkOrderId;
  if (!workOrderId) {
    return;
  }

  workspaceAnnouncement.value = "";
  await workOrders.openSelectedWorkOrder();

  const workspace = workOrders.activeWorkspace;
  if (
    workOrders.selectedWorkOrderId !== workOrderId ||
    workspace?.workOrder.id !== workOrderId
  ) {
    return;
  }

  workspaceAnnouncement.value =
    `Рабочее пространство ${workspace.workOrder.code} загружено`;
  await nextTick();
  detailsPanelRef.value?.focusHeading();
}
```

`onMounted()` оставляется отдельным и продолжает вызывать
`restoreOpenedWorkspace()` напрямую; это принципиально не использует
`openSelectedWorkspace()` и не перемещает focus.

- [ ] **Step 5: Перенести action/error и собрать workspacePane**

Из `.workOrderCard` полностью удалить blocks `.workOrderError` и
`.workOrderActionRow`.

Заменить текущий `<section class="mapPane">`:

```vue
<section class="workspacePane" aria-label="Рабочая область">
  <WorkspaceDetailsPanel
    v-if="workOrders.selectedWorkOrder"
    ref="detailsPanelRef"
    :work-order="workOrders.selectedWorkOrder"
    :workspace="workOrders.activeWorkspace"
    :is-opening="
      workOrders.openingWorkOrderId === workOrders.selectedWorkOrder.id
    "
    :is-open-action-disabled="workOrders.isOpeningWorkspace"
    :error-message="workOrders.selectedOpenWorkspaceError"
    @open="openSelectedWorkspace"
  />

  <p
    class="srOnly"
    data-test="workspace-announcement"
    aria-live="polite"
    aria-atomic="true"
  >
    {{ workspaceAnnouncement }}
  </p>

  <MapView
    v-if="workOrders.activeWorkspace"
    class="workspaceMap"
    mode="workspace"
    :workspace="workOrders.activeWorkspace"
    :workspace-key="workOrders.activeWorkspaceKey"
    :should-fit-workspace="
      workOrders.shouldFitWorkspace(workOrders.activeWorkspaceKey)
    "
    @workspace-fitted="workOrders.markWorkspaceFitted"
  />
  <MapView v-else class="workspaceMap" mode="empty" />
</section>
```

- [ ] **Step 6: Обновить layout CSS и удалить card-action CSS**

Удалить `.workOrderError`, `.workOrderActionRow`, `.openWorkspaceButton` и
`.openWorkspaceButton:disabled` rules. Заменить `.mapPane` на:

```css
.workspacePane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.workspaceMap {
  flex: 1 1 auto;
  min-height: 0;
}

.srOnly {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

В существующий `@media (max-width: 760px)` добавить controlled scrolling и
минимальную высоту карты:

```css
@media (max-width: 760px) {
  .editorShell {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 42%) minmax(420px, 1fr);
    overflow-y: auto;
  }

  .workOrdersPanel {
    border-right: 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  }

  .workspaceMap {
    min-height: 220px;
  }
}
```

Это сохраняет две колонки metadata внутри panel, не сжимает карту ниже 220px и
разрешает вертикальный scroll только когда viewport физически не вмещает список,
panel и карту.

- [ ] **Step 7: Запустить integration tests и подтвердить PASS**

```powershell
npm test -- src/components/WorkspaceDetailsPanel.test.ts src/components/EditorWorkOrdersView.test.ts src/stores/workOrders.test.ts
```

Expected: все tests трёх файлов PASS. Explicit open фокусирует heading, restore
не фокусирует, error/action отсутствуют в левой карточке, reselect показывает
сохранённый workspace.

- [ ] **Step 8: Проверить типы, lint, format и unstaged diff Task 3**

```powershell
npm run typecheck
npm run lint
npm run format:check
git -C ../.. diff --check
```

Expected: все команды exit 0. Если `format:check` находит только изменённые
frontend файлы, выполнить:

```powershell
npx prettier --write src/components/EditorWorkOrdersView.vue src/components/EditorWorkOrdersView.test.ts src/components/WorkspaceDetailsPanel.vue src/components/WorkspaceDetailsPanel.test.ts src/stores/workOrders.ts src/stores/workOrders.test.ts
```

Повторить targeted tests, typecheck и format check. Не индексировать изменения.

---

### Task 4: Remove Workspace Metadata Badge Without Affecting Other Map Modes

**Files:**

- Modify: `apps/frontend/src/components/MapView.vue:19-29`
- Modify: `apps/frontend/src/components/MapView.vue:162-177`
- Test: `apps/frontend/src/components/MapView.test.ts:174-218`
- Test: `apps/frontend/src/components/MapView.test.ts:220-272`

**Interfaces:**

- Consumes: existing props `mode`, `workspace`, `workspaceKey`, `shouldFitWorkspace`.
- Preserves: `workspaceFitted` event, workspace layers, AOI fit, empty badge, editing badge и realtime badge.
- Produces: в `workspace` mode `.badge` отсутствует и metadata text не создаётся.

- [ ] **Step 1: Изменить MapView expectations до реализации**

В empty-mode test добавить:

```ts
expect(wrapper.get(".badge").text()).toContain(
  "Карта готова. Выберите наряд в списке.",
);
```

В editing test после `await flushPromises()` добавить:

```ts
expect(wrapper.get(".badge").text()).toContain(
  "Слои загружены: 1. Выбран слой: Power lines",
);
```

В workspace test заменить assertions metadata text следующим block:

```ts
expect(wrapper.find(".badge").exists()).toBe(false);
expect(wrapper.text()).not.toContain("WO-001");
expect(wrapper.text()).not.toContain("Версия: open");
expect(wrapper.text()).not.toContain("Базовая ревизия сети: 1");
expect(wrapper.text()).not.toContain("Объекты: 1");
expect(wrapper.text()).not.toContain("Связи: 1");
```

Существующие assertions для `ensureWorkspaceLayers`, `setWorkspaceData`,
`fitWorkspaceToAoi`, `workspaceFitted` и отсутствия legacy loading сохранить.

- [ ] **Step 2: Запустить MapView test и подтвердить FAIL**

```powershell
npm test -- src/components/MapView.test.ts
```

Expected: workspace test FAIL, потому что `.badge` и длинная metadata string ещё рендерятся. Empty/editing assertions PASS.

- [ ] **Step 3: Ограничить общий badge non-workspace modes**

В template заменить badge:

```vue
<div v-if="props.mode !== 'workspace'" class="badge">
  {{ labelText }}
</div>
```

В `renderWorkspace()` оставить только map behavior:

```ts
function renderWorkspace(): void {
  if (!map.value || !props.workspace) {
    return;
  }

  ensureWorkspaceLayers(map.value);
  setWorkspaceData(map.value, props.workspace);

  if (props.shouldFitWorkspace && props.workspaceKey) {
    fitWorkspaceToAoi(map.value, props.workspace);
    emit("workspaceFitted", props.workspaceKey);
  }
}
```

Не менять `labelText` assignments для `empty`/`editing` и не менять
`realtimeBadge`.

- [ ] **Step 4: Запустить MapView и полный targeted frontend set**

```powershell
npm test -- src/components/MapView.test.ts
npm test -- src/components/WorkspaceDetailsPanel.test.ts src/components/EditorWorkOrdersView.test.ts src/components/MapView.test.ts src/stores/workOrders.test.ts
```

Expected: оба запуска PASS. Workspace map продолжает создавать layers и fit AOI,
но не выводит badge; empty/editing badge остаются.

- [ ] **Step 5: Проверить quality и unstaged diff Task 4**

```powershell
npm run typecheck
npm run lint
npm run format:check
git -C ../.. diff --check
```

Expected: все команды exit 0; изменения остаются unstaged.

---

### Task 5: Full Regression and Manual UX Gate

**Files:**

- Verify: `apps/frontend/src/components/WorkspaceDetailsPanel.vue`
- Verify: `apps/frontend/src/components/EditorWorkOrdersView.vue`
- Verify: `apps/frontend/src/components/MapView.vue`
- Verify: `apps/frontend/src/stores/workOrders.ts`
- Verify: соответствующие четыре test files

**Interfaces:**

- Consumes: завершённые Tasks 1-4.
- Produces: проверенный unstaged implementation set, готовый к пользовательскому review.

- [ ] **Step 1: Запустить полный frontend test suite**

Run from `apps/frontend`:

```powershell
npm test
```

Expected: Vitest exit 0, zero failed tests.

- [ ] **Step 2: Запустить статические quality gates**

```powershell
npm run typecheck
npm run lint
npm run format:check
npm run build
```

Expected: каждая команда exit 0; Vite production build завершается без TypeScript errors.

- [ ] **Step 3: Выполнить desktop manual scenario**

```powershell
npm run dev
```

Открыть URL, напечатанный Vite, и проверить последовательно:

1. Без selection panel отсутствует, empty map badge остаётся.
2. Selection показывает code/title/status/description и `Начать` над картой.
3. В левой карточке нет open action и open error.
4. `Начать` меняется на `Открываем…`, блокируется и не сдвигает layout.
5. Success показывает AOI, `Открыта`, base revision, objects и associations.
6. Workspace map не содержит длинный badge и fit выполняется по AOI.
7. Selection другого наряда показывает его preview и empty map.
8. Возврат к уже открытому наряду возвращает details/map без нового open request.

Expected: все восемь наблюдений соответствуют spec.

- [ ] **Step 4: Выполнить mobile и keyboard manual scenario**

В DevTools установить viewport width `760px`, затем `390px`:

1. Список остаётся сверху, panel и карта — снизу.
2. Metadata образуют две колонки, AOI занимает всю ширину.
3. Длинные title/AOI переносятся без горизонтального scroll.
4. Карта имеет высоту не меньше `220px`; при недостатке общей высоты работает вертикальный scroll shell.
5. Через `Tab` выбрать primary action и нажать `Enter`.
6. После success `document.activeElement` визуально соответствует panel heading.
7. После обычного reload восстановленный workspace не перехватывает focus.
8. Screen reader объявляет `Рабочее пространство WO-001 загружено` только после
   explicit open и не объявляет эту фразу при restore.

Expected: layout остаётся читаемым, клавиатурный порядок предсказуем, focus не теряется.

- [ ] **Step 5: Проверить итоговый diff и repository rule**

Run from repository root:

```powershell
git diff --check
git diff --cached --name-only
git status --short
```

Expected:

- `git diff --check` — exit 0 без output;
- `git diff --cached --name-only` — без output;
- `git status --short` показывает только unstaged/untracked файлы текущей работы и уже существующие пользовательские изменения;
- не выполнять `git add`, `git commit` или `git push`.

- [ ] **Step 6: Решить durable knowledge gate**

Сверить implementation с design spec. Если реализация следует этому плану без
нового устойчивого технического решения, не создавать agent-memory запись и не
запускать `/ingest repository-change`: design и plan уже сохраняют знания. Если
для корректной реализации пришлось изменить согласованные component boundaries,
store semantics или accessibility contract, остановиться и согласовать обновление
spec с пользователем до фиксации нового durable knowledge.

---

## Final Acceptance Checklist

- [ ] Новый backend/API request не добавлен.
- [ ] Preview использует только `WorkOrderSummary`.
- [ ] Panel отсутствует без selection.
- [ ] Action/error удалены из левой карточки и существуют в preview panel.
- [ ] Details содержат только AOI name, localized version, base revision и counts.
- [ ] Technical ids, raw statuses, extent, description-after-open и read-only copy отсутствуют.
- [ ] `openingWorkOrderId` точно связывает loading с инициировавшим нарядом.
- [ ] Stale response guards и session restore продолжают работать.
- [ ] Explicit open фокусирует heading и обновляет polite announcement.
- [ ] Restore при mount не меняет focus и не создаёт explicit-success announcement.
- [ ] Workspace `.badge` отсутствует; empty/editing/realtime badges сохранены.
- [ ] Desktop/mobile layout и keyboard scenario проверены.
- [ ] Targeted tests, full tests, typecheck, lint, format check и build прошли.
- [ ] Все изменения остаются unstaged; Git write commands не выполнялись.
