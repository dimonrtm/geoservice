import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { WorkspaceResponse } from "@/contracts/work-orders";

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
const restoreOpenedWorkspaceMock = vi.fn();

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

  it("restores opened workspace after assigned work orders load", async () => {
    const callOrder: string[] = [];
    loadAssignedMock.mockImplementation(async () => {
      callOrder.push("load");
    });
    restoreOpenedWorkspaceMock.mockImplementation(async () => {
      callOrder.push("restore");
    });

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [inProgressWorkOrder()];
    store.loadAssigned = loadAssignedMock;
    store.restoreOpenedWorkspace = restoreOpenedWorkspaceMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    mount(EditorWorkOrdersView);
    await flushPromises();

    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
    expect(restoreOpenedWorkspaceMock).toHaveBeenCalledTimes(1);
    expect(callOrder).toEqual(["load", "restore"]);
  });

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

    expect(
      wrapper.get('[data-test="workspace-details-panel"]').text(),
    ).toContain("WO-001");
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
        "Не удалось открыть рабочую версию. Обновите список или попробуйте ещё раз.",
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

  it("does not announce or move focus when selection changes during explicit open", async () => {
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

    let resolveOpen!: () => void;
    store.openSelectedWorkOrder = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveOpen = () => {
            store.openedWorkOrderId = "wo-1";
            store.openedEditVersionId = "ev-1";
            store.workspace = workspaceResponse();
            resolve();
          };
        }),
    );

    const sentinel = document.createElement("button");
    document.body.append(sentinel);
    sentinel.focus();
    const host = document.createElement("div");
    document.body.append(host);
    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView, { attachTo: host });

    await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
    store.selectWorkOrder("wo-2");
    resolveOpen();
    await flushPromises();

    expect(wrapper.get('[data-test="workspace-announcement"]').text()).toBe("");
    expect(document.activeElement).toBe(sentinel);
    expect(document.activeElement).not.toBe(
      wrapper.get('[data-test="workspace-details-title"]').element,
    );

    wrapper.unmount();
    host.remove();
    sentinel.remove();
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

    const sentinel = document.createElement("button");
    document.body.append(sentinel);
    sentinel.focus();
    const host = document.createElement("div");
    document.body.append(host);
    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView, { attachTo: host });
    await flushPromises();

    expect(document.activeElement).toBe(sentinel);
    expect(wrapper.get('[data-test="workspace-announcement"]').text()).toBe("");

    wrapper.unmount();
    host.remove();
    sentinel.remove();
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
});
