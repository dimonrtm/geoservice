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
const reopenSelectedWorkOrderMock = vi.fn();

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
    loadAssignedMock.mockReset();
    openSelectedWorkOrderMock.mockReset();
    restoreOpenedWorkspaceMock.mockReset();
    reopenSelectedWorkOrderMock.mockReset();
    sessionStorage.clear();
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

  it("refreshes assigned work orders through an accessible icon control", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();
    loadAssignedMock.mockClear();

    const refresh = wrapper.get('[data-test="refresh-work-orders"]');
    expect(refresh.attributes("aria-label")).toBe("Обновить");
    expect(refresh.attributes("aria-describedby")).toBeDefined();

    await refresh.trigger("click");
    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
  });

  it("exposes refresh loading state and blocks a second request", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.isLoading = true;
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    const refresh = wrapper.get('[data-test="refresh-work-orders"]');

    expect(refresh.attributes("disabled")).toBeDefined();
    expect(refresh.attributes("aria-busy")).toBe("true");
    expect(refresh.attributes("aria-label")).toBe("Обновление списка нарядов");
    expect(refresh.get("svg").classes()).toContain("uiControlLoader");

    await refresh.trigger("click");
    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
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

  it("routes the list retry action to loadAssigned", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.loadError = {
      summary: "Не удалось загрузить назначенные наряды.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "list-id" },
    };
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();
    loadAssignedMock.mockClear();

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Не удалось загрузить назначенные наряды",
    );
    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
  });

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

  it("routes sign-in errors to local logout", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const auth = useAuthStore();
    const store = useWorkOrdersStore();
    auth.logout = vi.fn();
    store.loadError = {
      summary: "Сессия завершена.",
      guidance: "Войдите снова.",
      action: { id: "sign-in", label: "Войти снова" },
      diagnostics: { code: "AUTH_REQUIRED", correlationId: "auth-id" },
    };
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(1);
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
    expect(
      wrapper
        .get('[data-test="workspace-open-action"]')
        .get('[data-ui-control-state="idle"]')
        .text(),
    ).toBe("Начать");
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

    expect(
      wrapper
        .get('[data-test="workspace-open-action"]')
        .get('[data-ui-control-state="idle"]')
        .text(),
    ).toBe("Продолжить");
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

  it("routes reopen from the selected workspace error", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [assignedWorkOrder()];
    store.selectedWorkOrderId = "wo-1";
    store.openWorkspaceErrorByWorkOrderId = {
      "wo-1": {
        summary: "Рабочая версия не найдена.",
        guidance: "Откройте рабочую версию заново.",
        action: { id: "reopen", label: "Открыть заново" },
        diagnostics: {
          code: "EDIT_VERSION_NOT_FOUND",
          correlationId: "workspace-id",
        },
      },
    };
    store.loadAssigned = loadAssignedMock;
    store.reopenSelectedWorkOrder = reopenSelectedWorkOrderMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(reopenSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
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
    expect(action.get('[data-ui-control-state="idle"]').text()).toBe("Начать");
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
});
