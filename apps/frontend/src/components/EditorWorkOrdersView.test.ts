import { useAuthStore } from "@/stores/auth";
import { editorTestContext } from "@/test/editorTestContext";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { WorkspaceResponse } from "@/contracts/work-orders";

vi.mock("@/components/MapView.vue", () => ({
  default: {
    name: "MapView",
    props: [
      "mode",
      "workspace",
      "workspaceKey",
      "shouldFitWorkspace",
      "workspaceInteractive",
    ],
    emits: ["workspaceFitted", "readyChange"],
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
        draftVersionToken: "1",
        hasPersistedChangeSet: false,
        basicValidation: null,
        changeSet: null,
        features: { type: "FeatureCollection", features: [] },
        associations: [],
      },
    },
  };
}

describe("EditorWorkOrdersView", () => {
  it("ignores a list request that finishes after the session changes", async () => {
    const context = editorTestContext();
    let complete!: () => void;
    context.workOrders.loadAssigned = vi.fn(async () => {
      await new Promise<void>((resolve) => {
        complete = resolve;
      });
      return context.workOrders.loadAssignedRequestSeq;
    });
    const reconcile = vi.spyOn(context.editorSession, "reconcileAssignments");
    const restore = vi.spyOn(context.editorSession, "restoreOpenedWorkspace");
    const { default: EditorWorkOrdersView } =
      await import("./EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    useAuthStore().sessionEpoch++;
    complete();
    await flushPromises();
    expect(reconcile).not.toHaveBeenCalled();
    expect(restore).not.toHaveBeenCalled();
    wrapper.unmount();
  });
  it("enables line interaction only for an opened workspace", async () => {
    const store = editorTestContext();
    store.workOrders.loadAssigned = vi.fn().mockResolvedValue(0);
    store.editorSession.restoreOpenedWorkspace = vi.fn();
    const { default: EditorWorkOrdersView } =
      await import("./EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    expect(
      wrapper.findComponent({ name: "MapView" }).props("workspaceInteractive"),
    ).not.toBe(true);
    store.seed(workspaceResponse());
    store.workOrders.selectedWorkOrderId =
      store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", true);
    await flushPromises();
    const commands = wrapper.get(
      '[data-test="workspace-edit-commands"]',
    ).element;
    expect(
      commands.compareDocumentPosition(
        wrapper.get('[data-test="map-view"]').element,
      ) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      wrapper.findComponent({ name: "MapView" }).props("workspaceInteractive"),
    ).toBe(true);
    wrapper.unmount();
  });

  it("does not inherit readiness from empty or removed map", async () => {
    const store = editorTestContext();
    store.workOrders.loadAssigned = vi.fn().mockResolvedValue(0);
    store.editorSession.restoreOpenedWorkspace = vi.fn();
    const { default: EditorWorkOrdersView } =
      await import("./EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", true);
    store.seed(workspaceResponse());
    store.workOrders.selectedWorkOrderId =
      store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", true);
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      true,
    );
    store.seed(null);
    await flushPromises();
    store.seed(workspaceResponse());
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.unmount();
  });

  it("keeps readiness on current workspace readback and hides commands on false", async () => {
    const store = editorTestContext();
    store.workOrders.loadAssigned = vi.fn().mockResolvedValue(0);
    store.editorSession.restoreOpenedWorkspace = vi.fn();
    store.seed(workspaceResponse());
    store.workOrders.selectedWorkOrderId =
      store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    const { default: EditorWorkOrdersView } =
      await import("./EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", true);
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      true,
    );
    store.seed(workspaceResponse());
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      true,
    );
    expect(
      wrapper.get('[data-test="save-edit"]').attributes("disabled"),
    ).toBeDefined();
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", false);
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.unmount();
  });

  it("hiding commands preserves recovery and does not send mutations", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const { useWorkspaceRecoveryStore } =
      await import("@/stores/workspaceRecovery");
    const { createRecoveryRecord } =
      await import("@/contracts/workspace-recovery");
    const { createLocalDraft } = await import("@/domain/workspaceDraft");
    const { workspaceFixture, target, candidate, geometry, commandId } =
      await import("@/test/workspaceEditFixture");
    const auth = useAuthStore();
    auth.token = "test";
    auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
    const store = editorTestContext();
    store.workOrders.loadAssigned = vi.fn().mockResolvedValue(0);
    store.editorSession.restoreOpenedWorkspace = vi.fn();
    store.seed(workspaceFixture());
    store.workOrders.selectedWorkOrderId =
      store.editorSession.openedWorkOrderId = target.workOrderId;
    store.editorSession.openedEditVersionId = target.editVersionId;
    store.editVersionDraft.localDraft = createLocalDraft(
      store.editor.snapshot!,
      target.featureId,
      1,
    );
    store.editVersionDraft.localDraft.candidateGeometry =
      structuredClone(candidate);
    const recovery = useWorkspaceRecoveryStore();
    const record = createRecoveryRecord(
      {
        actorId: "actor",
        target,
        request: {
          commandId,
          draftVersionToken: "revision-a",
          geometry: candidate,
        },
      },
      { geometry, vertexIndex: 1 },
    );
    recovery.records[record.key] = record;
    recovery.phases[record.key] = "unknown";
    const save = vi.spyOn(store.editVersionCommands, "saveLocalDraft");
    const revert = vi.spyOn(store.editVersionCommands, "confirmRevert");
    const retry = vi.spyOn(store.editVersionCommands, "retryPendingSave");
    const read = vi.spyOn(store.editVersionCommands, "refreshCurrentWorkspace");
    const snapshot = JSON.stringify({
      draft: store.editVersionDraft.localDraft,
      records: recovery.records,
      phases: recovery.phases,
    });
    const { default: EditorWorkOrdersView } =
      await import("./EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", true);
    await flushPromises();
    expect(wrapper.find('[data-test="retry-command"]').exists()).toBe(true);
    expect(
      wrapper.get('[data-test="save-edit"]').attributes("disabled"),
    ).toBeDefined();
    wrapper.findComponent({ name: "MapView" }).vm.$emit("readyChange", false);
    await flushPromises();
    expect(wrapper.find('[data-test="workspace-edit-commands"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-test="retry-command"]').exists()).toBe(false);
    expect(
      JSON.stringify({
        draft: store.editVersionDraft.localDraft,
        records: recovery.records,
        phases: recovery.phases,
      }),
    ).toBe(snapshot);
    for (const action of [save, revert, retry, read])
      expect(action).not.toHaveBeenCalled();
    wrapper.unmount();
    recovery.stopRuntime();
  });
  beforeEach(() => {
    vi.clearAllMocks();
    loadAssignedMock.mockReset().mockResolvedValue(0);
    openSelectedWorkOrderMock.mockReset();
    restoreOpenedWorkspaceMock.mockReset();
    reopenSelectedWorkOrderMock.mockReset();
    sessionStorage.clear();
    setActivePinia(createPinia());
    const auth = useAuthStore();
    auth.token = "token";
    auth.user = { id: "actor", email: "a@local", role: "editor" };
    editorTestContext().editorSession.reconcileAssignments = vi.fn();
  });

  it("loads work orders and renders empty map mode", async () => {
    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: "Описание",
        status: "assigned",
      },
    ];
    store.workOrders.loadAssigned = loadAssignedMock;

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
      return 0;
    });
    restoreOpenedWorkspaceMock.mockImplementation(async () => {
      callOrder.push("restore");
    });

    const store = editorTestContext();
    store.workOrders.items = [inProgressWorkOrder()];
    store.workOrders.loadAssigned = loadAssignedMock;
    store.editorSession.restoreOpenedWorkspace = restoreOpenedWorkspaceMock;

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
    loadAssignedMock.mockResolvedValue(0);

    const store = editorTestContext();
    store.workOrders.items = [assignedWorkOrder()];
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
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
    const store = editorTestContext();
    store.workOrders.isLoading = true;
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const state = wrapper.get(".panelState");
    expect(state.text()).toContain("Загружаем назначенные наряды");
    expect(state.attributes("aria-live")).toBe("polite");
    expect(state.attributes("aria-atomic")).toBe("true");
  });

  it("refreshes assigned work orders through an accessible icon control", async () => {
    const store = editorTestContext();
    store.workOrders.items = [];
    store.workOrders.loadAssigned = loadAssignedMock;

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
    const store = editorTestContext();
    store.workOrders.isLoading = true;
    store.workOrders.loadAssigned = loadAssignedMock;

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
    const store = editorTestContext();
    store.workOrders.items = [];
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const state = wrapper.get(".panelState");
    expect(state.text()).toContain("Назначенных нарядов нет.");
    expect(state.attributes("aria-live")).toBe("polite");
    expect(state.attributes("aria-atomic")).toBe("true");
  });

  it("selects and highlights a work order locally", async () => {
    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
    expect(
      wrapper
        .get('[data-test="work-order-wo-1"]')
        .element.closest(".workOrderCard")
        ?.classList.contains("isSelected"),
    ).toBe(true);
  });

  it("routes the list retry action to loadAssigned", async () => {
    const store = editorTestContext();
    store.workOrders.loadError = {
      summary: "Не удалось загрузить назначенные наряды.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "list-id" },
    };
    store.workOrders.loadAssigned = loadAssignedMock;

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

    const store = editorTestContext();
    store.workOrders.loadError = {
      summary: "Не удалось загрузить назначенные наряды.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "list-id" },
    };
    let loadCount = 0;
    store.workOrders.loadAssigned = vi.fn(async () => {
      loadCount += 1;
      if (loadCount === 2) {
        store.workOrders.items = [assignedWorkOrder()];
        store.workOrders.loadError = null;
      }
      return 0;
    });

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();

    await wrapper.get('[data-test="error-action"]').trigger("click");
    await flushPromises();

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
    expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
      "Проверка участка фидера",
    );
  });

  it("routes sign-in errors to local logout", async () => {
    const { useAuthStore } = await import("@/stores/auth");

    const auth = useAuthStore();
    const store = editorTestContext();
    auth.logout = vi.fn();
    store.workOrders.loadError = {
      summary: "Сессия завершена.",
      guidance: "Войдите снова.",
      action: { id: "sign-in", label: "Войти снова" },
      diagnostics: { code: "AUTH_REQUIRED", correlationId: "auth-id" },
    };
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(1);
  });

  it("exposes the selected work order as current without pressed state", async () => {
    const store = editorTestContext();
    store.workOrders.items = [
      assignedWorkOrder(),
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;

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
    const store = editorTestContext();
    store.workOrders.items = [
      { ...assignedWorkOrder(), description: "Описание выбранного наряда" },
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;
    store.editorSession.openSelectedWorkOrder = openSelectedWorkOrderMock;

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
    const store = editorTestContext();
    store.workOrders.items = [inProgressWorkOrder()];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;

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
    const store = editorTestContext();
    store.workOrders.items = [inProgressWorkOrder()];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse());
    store.workOrders.loadAssigned = loadAssignedMock;

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
    const store = editorTestContext();
    store.workOrders.items = [assignedWorkOrder()];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.editorSession.openWorkspaceErrorByWorkOrderId = {
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
    store.workOrders.loadAssigned = loadAssignedMock;
    store.editorSession.reopenSelectedWorkOrder = reopenSelectedWorkOrderMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(reopenSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
  });

  it("does not label a newly selected work order as opening", async () => {
    const store = editorTestContext();
    store.workOrders.items = [
      assignedWorkOrder(),
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.selectedWorkOrderId = "wo-2";
    store.editorSession.openingWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);

    const action = wrapper.get('[data-test="workspace-open-action"]');
    expect(action.get('[data-ui-control-state="idle"]').text()).toBe("Начать");
    expect(action.attributes("disabled")).toBeDefined();
  });

  it("focuses details and announces only after explicit open", async () => {
    const store = editorTestContext();
    store.workOrders.items = [assignedWorkOrder()];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;
    store.editorSession.openSelectedWorkOrder = vi.fn(async () => {
      store.workOrders.updateWorkOrderStatus("wo-1", "in_progress");
      store.editorSession.openedWorkOrderId = "wo-1";
      store.editorSession.openedEditVersionId = "ev-1";
      store.seed(workspaceResponse());
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
    const store = editorTestContext();
    store.workOrders.items = [
      assignedWorkOrder(),
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.workOrders.loadAssigned = loadAssignedMock;

    let resolveOpen!: () => void;
    store.editorSession.openSelectedWorkOrder = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveOpen = () => {
            store.editorSession.openedWorkOrderId = "wo-1";
            store.editorSession.openedEditVersionId = "ev-1";
            store.seed(workspaceResponse());
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
    store.workOrders.selectWorkOrder("wo-2");
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
    const store = editorTestContext();
    store.workOrders.items = [inProgressWorkOrder()];
    store.workOrders.loadAssigned = loadAssignedMock;
    store.editorSession.restoreOpenedWorkspace = vi.fn(async () => {
      store.workOrders.selectedWorkOrderId = "wo-1";
      store.editorSession.openedWorkOrderId = "wo-1";
      store.editorSession.openedEditVersionId = "ev-1";
      store.seed(workspaceResponse());
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
    const store = editorTestContext();
    store.workOrders.items = [
      inProgressWorkOrder(),
      {
        id: "wo-2",
        code: "WO-002",
        title: "Второй наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.workOrders.selectWorkOrder("wo-1");
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse());
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    store.workOrders.loadAssigned = loadAssignedMock;
    loadAssignedMock.mockResolvedValue(0);

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();

    await wrapper.get('[data-test="work-order-wo-2"]').trigger("click");
    await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

    expect(store.editor.snapshot).toBeNull();
    expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
      "empty",
    );
    expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(
      true,
    );
  });
});
