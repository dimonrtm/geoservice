# Sprint 1 Day 11 Мои наряды Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать экран `Мои наряды`, где `Editor` после login видит все назначенные ему `WorkOrders` и пустую карту с подложкой.

**Architecture:** Backend добавляет read-only endpoint `GET /api/v1/work-orders/assigned-to-me` поверх существующего `WorkOrderService`. Frontend заменяет прямой вход `Editor` в editing map на shell из списка work orders и пустой карты; выбор work order меняет только локальную подсветку в списке и не открывает `EditVersion`. CI/deployment остаются обычными: без dev-only переключателей и без ручных данных вне текущего seed/startup workflow.

**Tech Stack:** FastAPI, Pydantic v2, async SQLAlchemy 2, pytest, Vue 3, Pinia, Axios, Vitest, MapLibre, Docker Compose.

---

## File Structure

- Create `apps/backend/utility_service/use_cases/schemas/work_order/work_order_summary_out.py`: DTO одного элемента списка без audit fields.
- Create `apps/backend/utility_service/use_cases/schemas/work_order/assigned_work_orders_out.py`: DTO ответа `{ workOrders: [...] }`.
- Create `apps/backend/utility_service/use_cases/schemas/work_order/__init__.py`: public exports схем списка.
- Modify `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`: сортировать `list_assigned_to_user` по `updated_at DESC, code ASC`.
- Modify `apps/backend/utility_service/web_api/api/work_orders.py`: добавить `GET /api/v1/work-orders/assigned-to-me`.
- Modify `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`: route-level tests списка.
- Modify `apps/backend/utility_service/use_cases/tests/test_work_order_service.py`: unit coverage для списка и active editor guard.
- Create `apps/frontend/src/contracts/work-orders.ts`: frontend contract списка.
- Create `apps/frontend/src/api/workOrders.ts`: API client `fetchAssignedWorkOrders`.
- Create `apps/frontend/src/stores/workOrders.ts`: Pinia store для loading/error/items/selected.
- Create `apps/frontend/src/stores/workOrders.test.ts`: store unit tests.
- Modify `apps/frontend/package.json` and `apps/frontend/package-lock.json`: add component-test dependencies `@vue/test-utils` and `jsdom`.
- Modify `apps/frontend/vite.config.ts`: switch Vitest environment to `jsdom` for Vue component tests.
- Modify `apps/frontend/src/components/MapView.vue`: добавить `mode="empty" | "editing"`; в `empty` режиме создавать только карту и не грузить layers/features/realtime.
- Modify `apps/frontend/src/components/MapPageView.vue`: передавать `mode="editing"` в существующий editing сценарий.
- Create `apps/frontend/src/components/EditorWorkOrdersView.vue`: layout списка и пустой карты.
- Create `apps/frontend/src/components/EditorWorkOrdersView.test.ts`: component tests с mock `MapView`.
- Modify `apps/frontend/src/App.vue`: показывать `EditorWorkOrdersView` для `Editor`.
- Modify `docs/release_1/sprint_1/README.md`: добавить ссылки на design spec и implementation plan Интенсива 11.

Коммиты не выполнять без явного разрешения пользователя.

## Task 1: Backend Response Schemas

**Files:**
- Create: `apps/backend/utility_service/use_cases/schemas/work_order/work_order_summary_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/work_order/assigned_work_orders_out.py`
- Create: `apps/backend/utility_service/use_cases/schemas/work_order/__init__.py`
- Test: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Write failing API response-contract test**

Add this helper to `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`:

```python
def work_order_summary(
    *,
    code: str = "WO-001",
    status: str = "assigned",
):
    return SimpleNamespace(
        id=uuid4(),
        code=code,
        title=f"Наряд {code}",
        description=f"Описание {code}",
        status=SimpleNamespace(value=status),
    )
```

Add the test:

```python
def test_list_assigned_to_me_returns_compact_work_orders_without_audit_fields() -> None:
    auth_service, token, user_id = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    assigned = work_order_summary(code="WO-002", status="in_progress")
    work_order_service.list_assigned_to_editor.return_value = [assigned]

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "workOrders": [
            {
                "id": str(assigned.id),
                "code": "WO-002",
                "title": "Наряд WO-002",
                "description": "Описание WO-002",
                "status": "in_progress",
            }
        ]
    }
    assert "updatedAt" not in payload["workOrders"][0]
    assert "createdAt" not in payload["workOrders"][0]
    work_order_service.list_assigned_to_editor.assert_awaited_once_with(user_id)
```

Update `build_app(...)` signature to accept `work_order_service` and override `get_work_order_service`:

```python
def build_app(
    auth_service: object,
    edit_version_service: object,
    workspace_service: object | None = None,
    work_order_service: object | None = None,
) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(work_orders_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_edit_version_service] = lambda: edit_version_service
    if workspace_service is not None:
        app.dependency_overrides[get_workspace_service] = lambda: workspace_service
    if work_order_service is not None:
        app.dependency_overrides[get_work_order_service] = lambda: work_order_service
    return app
```

Also import `get_work_order_service` from `utility_service.use_cases.deps`.

- [ ] **Step 2: Run the failing test**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_work_orders_api.py::test_list_assigned_to_me_returns_compact_work_orders_without_audit_fields -q
```

Expected: FAIL because `get_work_order_service` is not imported in the test or route does not exist yet.

- [ ] **Step 3: Add backend schemas**

Create `apps/backend/utility_service/use_cases/schemas/work_order/work_order_summary_out.py`:

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkOrderSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    title: str
    description: str | None
    status: str
```

Create `apps/backend/utility_service/use_cases/schemas/work_order/assigned_work_orders_out.py`:

```python
from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.work_order.work_order_summary_out import (
    WorkOrderSummaryOut,
)


class AssignedWorkOrdersOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    work_orders: list[WorkOrderSummaryOut] = Field(serialization_alias="workOrders")
```

Create `apps/backend/utility_service/use_cases/schemas/work_order/__init__.py`:

```python
from .assigned_work_orders_out import AssignedWorkOrdersOut
from .work_order_summary_out import WorkOrderSummaryOut

__all__ = [
    "AssignedWorkOrdersOut",
    "WorkOrderSummaryOut",
]
```

- [ ] **Step 4: Run schema import check**

Run:

```powershell
cd apps/backend
python -c "from utility_service.use_cases.schemas.work_order import AssignedWorkOrdersOut, WorkOrderSummaryOut; print(AssignedWorkOrdersOut.__name__, WorkOrderSummaryOut.__name__)"
```

Expected: prints `AssignedWorkOrdersOut WorkOrderSummaryOut`.

## Task 2: Backend Endpoint And Authorization

**Files:**
- Modify: `apps/backend/utility_service/web_api/api/work_orders.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Add route tests for empty list and reviewer denial**

Add:

```python
def test_list_assigned_to_me_returns_empty_list() -> None:
    auth_service, token, user_id = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    work_order_service.list_assigned_to_editor.return_value = []

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"workOrders": []}
    work_order_service.list_assigned_to_editor.assert_awaited_once_with(user_id)


def test_reviewer_is_denied_before_assigned_work_orders_service_call() -> None:
    auth_service, token, _ = auth_context("reviewer")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    work_order_service.list_assigned_to_editor.assert_not_awaited()
```

- [ ] **Step 2: Run route tests and verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: the new list tests FAIL until route is added; existing tests still PASS.

- [ ] **Step 3: Add route implementation**

In `apps/backend/utility_service/web_api/api/work_orders.py`, update imports:

```python
from utility_service.use_cases.deps import (
    get_edit_version_service,
    get_work_order_service,
    get_workspace_service,
)
from utility_service.use_cases.schemas.work_order import (
    AssignedWorkOrdersOut,
    WorkOrderSummaryOut,
)
from utility_service.use_cases.services.work_order_service import WorkOrderService
```

Add route before `/{work_order_id}/edit-versions` so the static path wins:

```python
@work_orders_router.get(
    "/assigned-to-me",
    response_model=AssignedWorkOrdersOut,
)
async def list_assigned_to_me(
    user: Any = Depends(require_editor),
    work_order_service: WorkOrderService = Depends(get_work_order_service),
) -> AssignedWorkOrdersOut:
    work_orders = await work_order_service.list_assigned_to_editor(user.id)
    return AssignedWorkOrdersOut(
        work_orders=[
            WorkOrderSummaryOut(
                id=work_order.id,
                code=work_order.code,
                title=work_order.title,
                description=work_order.description,
                status=getattr(work_order.status, "value", work_order.status),
            )
            for work_order in work_orders
        ]
    )
```

- [ ] **Step 4: Run backend route tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

## Task 3: Backend Sorting And Service Coverage

**Files:**
- Modify: `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py`
- Modify: `apps/backend/utility_service/use_cases/tests/test_work_order_service.py`
- Optional Test: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Add service unit test for assigned list**

Add to `test_work_order_service.py`:

```python
def test_list_assigned_to_editor_loads_actor_and_returns_repository_result() -> None:
    actor = user()
    assigned = [
        work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS),
        work_order(actor.id, status=WorkOrderStatus.ASSIGNED),
    ]
    work_order_repository = AsyncMock()
    work_order_repository.list_assigned_to_user.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    result = asyncio.run(service.list_assigned_to_editor(actor.id))

    assert result == assigned
    user_repository.get_by_id.assert_awaited_once_with(actor.id)
    work_order_repository.list_assigned_to_user.assert_awaited_once_with(actor.id)
```

Add denial test:

```python
def test_list_assigned_to_editor_rejects_reviewer() -> None:
    actor = user(UserRole.REVIEWER)
    work_order_repository = AsyncMock()
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.list_assigned_to_editor(actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    work_order_repository.list_assigned_to_user.assert_not_awaited()
```

- [ ] **Step 2: Run service tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_work_order_service.py -q
```

Expected: PASS if existing service method is already correct.

- [ ] **Step 3: Update repository sorting**

In `WorkOrderRepository.list_assigned_to_user`, change order:

```python
async def list_assigned_to_user(self, user_id: UUID) -> list[WorkOrder]:
    result = await self.session.execute(
        select(WorkOrder)
        .where(WorkOrder.assignee_user_id == user_id)
        .order_by(WorkOrder.updated_at.desc(), WorkOrder.code.asc())
    )
    return list(result.scalars().all())
```

- [ ] **Step 4: Add route-level sorting assertion with mocked service**

Because route tests mock the service, they cannot prove repository sorting. Keep route test focused on preserving service order:

```python
def test_list_assigned_to_me_preserves_service_order() -> None:
    auth_service, token, _ = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    work_order_service.list_assigned_to_editor.return_value = [
        work_order_summary(code="WO-002", status="in_progress"),
        work_order_summary(code="WO-001", status="assigned"),
    ]

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert [item["code"] for item in response.json()["workOrders"]] == [
        "WO-002",
        "WO-001",
    ]
```

Repository sorting is verified in integration/DB suites when DB tests run.

- [ ] **Step 5: Run backend focused tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_work_order_service.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

## Task 4: Frontend API And Store

**Files:**
- Create: `apps/frontend/src/contracts/work-orders.ts`
- Create: `apps/frontend/src/api/workOrders.ts`
- Create: `apps/frontend/src/stores/workOrders.ts`
- Create: `apps/frontend/src/stores/workOrders.test.ts`

- [ ] **Step 1: Write failing store tests**

Create `apps/frontend/src/stores/workOrders.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const fetchAssignedWorkOrdersMock = vi.fn();

vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
}));

describe("work orders store", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("loads assigned work orders and clears previous error", async () => {
    fetchAssignedWorkOrdersMock.mockResolvedValue({
      workOrders: [
        {
          id: "wo-1",
          code: "WO-001",
          title: "Проверка участка фидера",
          description: "Описание",
          status: "assigned",
        },
      ],
    });

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toHaveLength(1);
    expect(store.items[0].code).toBe("WO-001");
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBeNull();
  });

  it("selects a work order locally without API calls", async () => {
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

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(store.selectedWorkOrder?.code).toBe("WO-001");
    expect(fetchAssignedWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("keeps a user-facing error when loading fails", async () => {
    fetchAssignedWorkOrdersMock.mockRejectedValue(new Error("network"));

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBe(
      "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.",
    );
  });
});
```

- [ ] **Step 2: Run store tests and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts
```

Expected: FAIL because `@/stores/workOrders` and `@/api/workOrders` do not exist.

- [ ] **Step 3: Add frontend contract and API client**

Create `apps/frontend/src/contracts/work-orders.ts`:

```ts
export type WorkOrderStatus = "assigned" | "in_progress";

export type WorkOrderSummary = {
  id: string;
  code: string;
  title: string;
  description: string | null;
  status: WorkOrderStatus;
};

export type AssignedWorkOrdersResponse = {
  workOrders: WorkOrderSummary[];
};
```

Create `apps/frontend/src/api/workOrders.ts`:

```ts
import { http } from "@/api/http";
import type { AssignedWorkOrdersResponse } from "@/contracts/work-orders";

export async function fetchAssignedWorkOrders() {
  const response = await http.get<AssignedWorkOrdersResponse>(
    "/api/v1/work-orders/assigned-to-me",
  );
  return response.data;
}
```

- [ ] **Step 4: Add Pinia store**

Create `apps/frontend/src/stores/workOrders.ts`:

```ts
import { defineStore } from "pinia";

import { fetchAssignedWorkOrders } from "@/api/workOrders";
import type { WorkOrderSummary } from "@/contracts/work-orders";

type WorkOrdersState = {
  items: WorkOrderSummary[];
  isLoading: boolean;
  errorMessage: string | null;
  selectedWorkOrderId: string | null;
};

export const useWorkOrdersStore = defineStore("workOrders", {
  state: (): WorkOrdersState => ({
    items: [],
    isLoading: false,
    errorMessage: null,
    selectedWorkOrderId: null,
  }),
  getters: {
    selectedWorkOrder: (state) =>
      state.items.find((item) => item.id === state.selectedWorkOrderId) ?? null,
  },
  actions: {
    async loadAssigned() {
      this.isLoading = true;
      this.errorMessage = null;
      try {
        const result = await fetchAssignedWorkOrders();
        this.items = result.workOrders;
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        ) {
          this.selectedWorkOrderId = null;
        }
      } catch {
        this.items = [];
        this.errorMessage =
          "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.";
      } finally {
        this.isLoading = false;
      }
    },
    selectWorkOrder(workOrderId: string) {
      this.selectedWorkOrderId = workOrderId;
    },
    clearSelection() {
      this.selectedWorkOrderId = null;
    },
  },
});
```

- [ ] **Step 5: Run store tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts
```

Expected: PASS.

## Task 5: Empty Map Mode

**Files:**
- Modify: `apps/frontend/src/components/MapView.vue`
- Modify: `apps/frontend/src/components/MapPageView.vue`

- [ ] **Step 1: Add `mode` prop to `MapView`**

In `MapView.vue`, add props:

```ts
const props = withDefaults(
  defineProps<{
    mode?: "empty" | "editing";
  }>(),
  {
    mode: "editing",
  },
);
```

Wrap toolbar with editing mode:

```vue
<div v-if="props.mode === 'editing'" class="toolbar">
```

Wrap realtime badge with editing mode:

```vue
<div
  v-if="props.mode === 'editing'"
  class="realtimeBadge"
  :class="realtimeBadgeClass"
>
  {{ realtimeStatusText }}
</div>
```

In `onMounted`, after map creation:

```ts
if (props.mode === "empty") {
  labelText.value = "Карта готова. Выберите наряд в списке.";
  return;
}
```

This return must happen before `loadLayers()`, `reloadFeatures(...)`, `syncRealtimeLayer(...)`, `bindActiveLayerClick(...)`, and editing overlay sync.

- [ ] **Step 2: Keep existing map page in editing mode**

Modify `MapPageView.vue`:

```vue
<MapView class="mapSlot" mode="editing" />
```

- [ ] **Step 3: Run frontend typecheck**

Run:

```powershell
cd apps/frontend
npm run typecheck
```

Expected: PASS.

## Task 6: Editor Work Orders View

**Files:**
- Modify: `apps/frontend/package.json`
- Modify: `apps/frontend/package-lock.json`
- Modify: `apps/frontend/vite.config.ts`
- Create: `apps/frontend/src/components/EditorWorkOrdersView.vue`
- Create: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`

- [ ] **Step 1: Add Vue component test dependencies and DOM environment**

Run:

```powershell
cd apps/frontend
npm install -D @vue/test-utils jsdom
```

Expected: `package.json` and `package-lock.json` include `@vue/test-utils` and `jsdom`.

Modify `apps/frontend/vite.config.ts`:

```ts
test: {
  environment: "jsdom",
},
```

- [ ] **Step 2: Run existing frontend tests after environment switch**

Run:

```powershell
cd apps/frontend
npm test
```

Expected: PASS. Existing store/composable tests must keep passing in `jsdom`.

- [ ] **Step 3: Write component tests**

Create `apps/frontend/src/components/EditorWorkOrdersView.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/MapView.vue", () => ({
  default: {
    name: "MapView",
    props: ["mode"],
    template: '<div data-test="map-view" :data-mode="mode"></div>',
  },
}));

const loadAssignedMock = vi.fn();

describe("EditorWorkOrdersView", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("loads work orders and renders empty map mode", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: "Описание",
        status: "assigned",
      },
    ];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } = await import(
      "@/components/EditorWorkOrdersView.vue"
    );
    const wrapper = mount(EditorWorkOrdersView);

    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("Мои наряды");
    expect(wrapper.text()).toContain("WO-001");
    expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
      "empty",
    );
  });

  it("selects and highlights a work order locally", async () => {
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
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } = await import(
      "@/components/EditorWorkOrdersView.vue"
    );
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(wrapper.get('[data-test="work-order-wo-1"]').classes()).toContain(
      "isSelected",
    );
  });
});
```

- [ ] **Step 4: Run component test and verify failure**

Run:

```powershell
cd apps/frontend
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: FAIL because `EditorWorkOrdersView.vue` does not exist yet.

- [ ] **Step 5: Add component implementation**

Create `apps/frontend/src/components/EditorWorkOrdersView.vue`:

```vue
<script setup lang="ts">
import { onMounted } from "vue";

import MapView from "@/components/MapView.vue";
import { useWorkOrdersStore } from "@/stores/workOrders";

const workOrders = useWorkOrdersStore();

onMounted(() => {
  void workOrders.loadAssigned();
});

function statusLabel(status: string): string {
  if (status === "in_progress") {
    return "В работе";
  }
  return "Назначен";
}
</script>

<template>
  <div class="editorShell">
    <aside class="workOrdersPanel" aria-label="Мои наряды">
      <div class="panelHeader">
        <h1>Мои наряды</h1>
        <button class="refreshButton" type="button" @click="workOrders.loadAssigned">
          Обновить
        </button>
      </div>

      <div v-if="workOrders.isLoading" class="panelState">
        Загружаем назначенные наряды...
      </div>

      <div v-else-if="workOrders.errorMessage" class="panelState isError">
        <span>{{ workOrders.errorMessage }}</span>
        <button class="retryButton" type="button" @click="workOrders.loadAssigned">
          Повторить
        </button>
      </div>

      <div v-else-if="workOrders.items.length === 0" class="panelState">
        Назначенных нарядов нет.
      </div>

      <ul v-else class="workOrderList">
        <li v-for="workOrder in workOrders.items" :key="workOrder.id">
          <button
            class="workOrderButton"
            :class="{ isSelected: workOrders.selectedWorkOrderId === workOrder.id }"
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
        </li>
      </ul>
    </aside>

    <section class="mapPane" aria-label="Карта">
      <MapView mode="empty" />
    </section>
  </div>
</template>
```

Add scoped CSS with stable layout:

```css
.editorShell {
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
}

.workOrdersPanel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(15, 23, 42, 0.1);
  background: #f8fafc;
}

.panelHeader {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.panelHeader h1 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}

.refreshButton,
.retryButton {
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.panelState {
  padding: 16px;
  color: #475569;
  font-size: 14px;
  line-height: 1.4;
}

.panelState.isError {
  display: grid;
  gap: 10px;
  color: #991b1b;
}

.workOrderList {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 8px;
  margin: 0;
  padding: 12px;
  list-style: none;
}

.workOrderButton {
  width: 100%;
  display: grid;
  gap: 5px;
  text-align: left;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
}

.workOrderButton.isSelected {
  border-color: #166534;
  box-shadow: inset 3px 0 0 #166534;
}

.workOrderCode {
  font-size: 12px;
  font-weight: 800;
  color: #166534;
}

.workOrderTitle {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.workOrderStatus,
.workOrderDescription {
  font-size: 13px;
  line-height: 1.35;
  color: #475569;
}

.mapPane {
  min-width: 0;
  min-height: 0;
}

@media (max-width: 760px) {
  .editorShell {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 42%) minmax(260px, 1fr);
  }

  .workOrdersPanel {
    border-right: 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  }
}
```

- [ ] **Step 6: Run component test**

Run:

```powershell
cd apps/frontend
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS.

## Task 7: App Routing For Editor

**Files:**
- Modify: `apps/frontend/src/App.vue`
- Optional Test: `apps/frontend/src/App.test.ts`

- [ ] **Step 1: Replace editor entry component**

In `App.vue`, replace:

```ts
import MapPageView from "./components/MapPageView.vue";
```

with:

```ts
import EditorWorkOrdersView from "./components/EditorWorkOrdersView.vue";
```

Replace template branch:

```vue
<MapPageView v-if="showEditorWorkspace" class="mapSlot" />
```

with:

```vue
<EditorWorkOrdersView v-if="showEditorWorkspace" class="mapSlot" />
```

Keep `ReviewerHome` branch unchanged.

- [ ] **Step 2: Run frontend tests and typecheck**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts
npm run typecheck
```

Expected: PASS.

## Task 8: Sprint Documentation Link

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`

- [ ] **Step 1: Add links to Day 11 design and implementation plan**

Add a compact entry near the other Sprint 1 day links:

```markdown
- Интенсив 11 Мои наряды: [design](2026-06-22-sprint-1-day-11-my-work-orders-design.md), [implementation plan](2026-06-22-sprint-1-day-11-my-work-orders-implementation-plan.md)
```

- [ ] **Step 2: Verify links resolve**

Run:

```powershell
Test-Path docs/release_1/sprint_1/2026-06-22-sprint-1-day-11-my-work-orders-design.md
Test-Path docs/release_1/sprint_1/2026-06-22-sprint-1-day-11-my-work-orders-implementation-plan.md
```

Expected: both print `True`.

## Task 9: CI And Deployment Verification

**Files:**
- No production files unless a verification failure identifies a real issue.

- [ ] **Step 1: Run focused backend tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_work_order_service.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: PASS.

- [ ] **Step 2: Run focused frontend tests**

Run:

```powershell
cd apps/frontend
npm test -- src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts
```

Expected: PASS.

- [ ] **Step 3: Run frontend typecheck/build**

Run:

```powershell
cd apps/frontend
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 4: Run broader backend suite**

Run:

```powershell
cd apps/backend
python -m pytest -q
```

Expected: PASS, with DB integration tests skipped when DB env is not enabled.

- [ ] **Step 5: Docker Compose smoke**

Run the existing project startup command:

```powershell
.\scripts\dev.cmd
```

Expected: backend and frontend start through the standard workflow. Login as seeded `Editor`; the first authenticated editor view shows `Мои наряды`, a list containing assigned work orders from seed, and a blank base map. Selecting a work order highlights only the list item and does not call `POST /api/v1/work-orders/{id}/edit-versions`.

If the local environment cannot run Docker Compose, record that limitation in the final implementation report and rely on CI plus targeted tests for this pass.

## Task 10: Post-Implementation Knowledge Check

**Files:**
- Review: `docs/agent-memory/file-map.md`
- Optional via explicit workflow only: `Code_wiki/` entries through `/ingest repository-change`

- [ ] **Step 1: Decide whether repository-change ingest is needed**

After implementation, inspect whether the completed work creates durable technical knowledge not already preserved by code, tests, design spec, implementation plan, and existing `Code_wiki`.

Expected decision: likely yes if this becomes the first public `assigned-to-me` Work Orders list API and frontend editor shell. If yes, run `/ingest repository-change` after implementation. If existing `Code_wiki` already captures the final pattern and no new durable relationship appears, do not ingest.

- [ ] **Step 2: Decide whether agent memory is needed**

Do not create memory for task completion, changed files, or test logs. Consider agent memory only if implementation uncovers a non-obvious bug root cause, stable cross-file pattern, or operational constraint useful for future work.

## Plan Self-Review

- Spec coverage: backend list endpoint, compact response without audit fields, sorting by internal `updated_at`, all assigned statuses, no `EditVersion` open, list-only selection, empty map with base layer, loading/empty/error states, reviewer branch, CI/build/deployment gates are covered.
- Placeholder scan: no unresolved markers or missing file paths. Component-test dependencies and `jsdom` setup are explicit package/vite changes.
- Type consistency: backend uses `AssignedWorkOrdersOut.work_orders` with alias `workOrders`; frontend uses `AssignedWorkOrdersResponse.workOrders`; `WorkOrderStatus` values are `assigned` and `in_progress`; route path is consistently `/api/v1/work-orders/assigned-to-me`.

## Execution Handoff

Plan complete and saved to `docs/release_1/sprint_1/2026-06-22-sprint-1-day-11-my-work-orders-implementation-plan.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.
