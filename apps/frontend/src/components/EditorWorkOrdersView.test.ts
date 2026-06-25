import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/MapView.vue", () => ({
  default: {
    name: "MapView",
    props: ["mode", "workspace", "workspaceKey", "shouldFitWorkspace"],
    emits: ["workspaceFitted"],
    template:
      '<div data-test="map-view" :data-mode="mode" :data-workspace-key="workspaceKey"></div>',
  },
}));

const loadAssignedMock = vi.fn();
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

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
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

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(
      wrapper
        .get('[data-test="work-order-wo-1"]')
        .element.closest(".workOrderCard")
        ?.classList.contains("isSelected"),
    ).toBe(true);
  });

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
    expect(
      wrapper.get('[data-test="map-view"]').attributes("data-workspace-key"),
    ).toBe("wo-1:ev-1");
  });

  it("shows open error near selected work order", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [assignedWorkOrder()];
    store.selectedWorkOrderId = "wo-1";
    store.openWorkspaceErrorByWorkOrderId = {
      "wo-1":
        "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
    };
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    expect(
      wrapper.get('[data-test="open-work-order-error-wo-1"]').text(),
    ).toContain("Не удалось открыть рабочую версию");
  });
});
