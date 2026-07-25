import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import type { WorkspaceResponse } from "@/contracts/work-orders";

const fetchAssignedWorkOrdersMock = vi.fn();
const openEditVersionMock = vi.fn();
const fetchWorkspaceMock = vi.fn();
const SELECTED_WORK_ORDER_STORAGE_KEY = "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";

vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
  openEditVersion: openEditVersionMock,
  fetchWorkspace: fetchWorkspaceMock,
}));

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

function workspaceResponse(
  workOrderId = "wo-1",
  editVersionId = "ev-1",
): WorkspaceResponse {
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

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

function apiFailure(
  code: string,
  status: number,
  correlationId = "request-id",
) {
  return {
    isAxiosError: true,
    response: {
      status,
      headers: { "x-correlation-id": correlationId },
      data: { code, message: `Причина ${code}`, correlationId },
    },
  };
}

function networkFailure() {
  return { isAxiosError: true };
}

describe("work orders store", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    sessionStorage.clear();
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
    expect(store.items[0]).toMatchObject({ code: "WO-001" });
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toBeNull();
  });

  it("resets user-scoped state and invalidates pending requests", async () => {
    sessionStorage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1" }),
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
        title: "Assigned work",
        description: "Old user work order",
        status: "assigned",
      },
    ];
    store.isLoading = true;
    store.loadError = {
      summary: "load failed",
      guidance: null,
      action: null,
      diagnostics: { code: null, correlationId: null },
    };
    store.selectedWorkOrderId = "wo-1";
    store.openedWorkOrderId = "wo-1";
    store.openedEditVersionId = "ev-1";
    store.workspace = workspaceResponse();
    store.openingWorkOrderId = "wo-1";
    store.openWorkspaceErrorByWorkOrderId = {
      "wo-1": {
        summary: "open failed",
        guidance: null,
        action: null,
        diagnostics: { code: null, correlationId: null },
      },
    };
    store.openWorkspaceErrorOperationByWorkOrderId = { "wo-1": "open" };
    store.lastFittedWorkspaceKey = "wo-1:ev-1";
    store.openWorkspaceRequestSeq = 7;
    store.loadAssignedRequestSeq = 11;

    store.reset();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toBeNull();
    expect(store.selectedWorkOrderId).toBeNull();
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.openedEditVersionId).toBeNull();
    expect(store.workspace).toBeNull();
    expect(store.openingWorkOrderId).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
    expect(store.openWorkspaceErrorByWorkOrderId).toEqual({});
    expect(store.openWorkspaceErrorOperationByWorkOrderId).toEqual({});
    expect(store.lastFittedWorkspaceKey).toBeNull();
    expect(store.openWorkspaceRequestSeq).toBe(8);
    expect(store.loadAssignedRequestSeq).toBe(12);
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBeNull();
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("can reset in-memory state while preserving work order session markers", async () => {
    sessionStorage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1" }),
    );
    sessionStorage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.selectedWorkOrderId = "wo-1";
    store.openedWorkOrderId = "wo-1";
    store.openedEditVersionId = "ev-1";
    store.workspace = workspaceResponse();

    store.reset({
      preserveOpenedWorkspace: true,
      preserveSelectedWorkOrder: true,
    });

    expect(store.selectedWorkOrderId).toBeNull();
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.openedEditVersionId).toBeNull();
    expect(store.workspace).toBeNull();
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
  });

  it("persists the selected work order in session storage", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    store.selectWorkOrder("wo-1");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
  });

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

  it("keeps a user-facing error when loading fails", async () => {
    fetchAssignedWorkOrdersMock.mockRejectedValue(networkFailure());

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toMatchObject({
      summary: "Не удалось загрузить назначенные наряды.",
      action: { id: "retry", label: "Повторить" },
    });
  });

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
    expect(store.items[0]?.status).toBe("in_progress");
    expect(store.openedWorkOrderId).toBe("wo-1");
    expect(store.openedEditVersionId).toBe("ev-1");
    expect(store.activeWorkspace?.workOrder.code).toBe("WO-001");
    expect(store.activeWorkspaceKey).toBe("wo-1:ev-1");
    expect(store.selectedOpenWorkspaceError).toBeNull();
    expect(store.openingWorkOrderId).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
  });

  it("maps a missing work order to refresh", async () => {
    openEditVersionMock.mockRejectedValue(
      apiFailure("WORK_ORDER_NOT_FOUND", 404),
    );
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.selectWorkOrder("wo-1");

    await store.openSelectedWorkOrder();

    expect(store.selectedOpenWorkspaceError?.action?.id).toBe("refresh");
    expect(store.selectedOpenWorkspaceError?.diagnostics.correlationId).toBe(
      "request-id",
    );
    expect(store.selectedOpenWorkspaceErrorOperation).toBe("open");
  });

  it("persists opened workspace identifiers after successful open", async () => {
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

    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBe(
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
  });

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

  it.each([
    "{invalid-json",
    JSON.stringify({}),
    JSON.stringify({ workOrderId: "" }),
    JSON.stringify({ workOrderId: 42 }),
  ])(
    "removes an invalid selected work order marker: %s",
    async (storedValue) => {
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
      expect(
        sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY),
      ).toBeNull();
      expect(fetchWorkspaceMock).not.toHaveBeenCalled();
    },
  );

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

  it("restores opened workspace from session storage without opening edit version again", async () => {
    sessionStorage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    fetchWorkspaceMock.mockResolvedValue(workspaceResponse("wo-1", "ev-1"));

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: null,
        status: "in_progress",
      },
    ];

    await store.restoreOpenedWorkspace();

    expect(openEditVersionMock).not.toHaveBeenCalled();
    expect(fetchWorkspaceMock).toHaveBeenCalledWith("wo-1", "ev-1");
    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(store.openedWorkOrderId).toBe("wo-1");
    expect(store.openedEditVersionId).toBe("ev-1");
    expect(store.activeWorkspace?.workOrder.code).toBe("WO-001");
    expect(store.activeWorkspaceKey).toBe("wo-1:ev-1");
    expect(store.openingWorkOrderId).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
  });

  it("clears persisted workspace when saved work order is no longer assigned", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-missing", editVersionId: "ev-1" }),
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

    expect(fetchWorkspaceMock).not.toHaveBeenCalled();
    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBeNull();
    expect(store.selectedWorkOrderId).toBeNull();
    expect(store.activeWorkspace).toBeNull();
  });

  it("clears a stale marker and offers reopen when the edit version disappeared", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    fetchWorkspaceMock.mockRejectedValue(
      apiFailure("EDIT_VERSION_NOT_FOUND", 404),
    );
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "in_progress",
      },
    ];

    await store.restoreOpenedWorkspace();

    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBeNull();
    expect(store.selectedOpenWorkspaceError?.action?.id).toBe("reopen");
    expect(store.selectedOpenWorkspaceErrorOperation).toBe("restore");
  });

  it("preserves the marker and retries the original restore after a network failure", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    fetchWorkspaceMock.mockRejectedValueOnce(networkFailure());
    fetchWorkspaceMock.mockResolvedValueOnce(workspaceResponse("wo-1", "ev-1"));
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "in_progress",
      },
    ];

    await store.restoreOpenedWorkspace();
    await store.retrySelectedWorkspaceError();

    expect(openEditVersionMock).not.toHaveBeenCalled();
    expect(fetchWorkspaceMock).toHaveBeenCalledTimes(2);
    expect(store.activeWorkspace?.workOrder.id).toBe("wo-1");
  });

  it("keeps action retry available when workspace loading fails after open", async () => {
    openEditVersionMock.mockResolvedValue(openEditVersionResponse());
    fetchWorkspaceMock.mockRejectedValue(networkFailure());

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

    expect(store.items[0]?.status).toBe("in_progress");
    expect(store.workspace).toBeNull();
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.selectedOpenWorkspaceError?.action?.id).toBe("retry");
    expect(store.openingWorkOrderId).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
  });

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

  it("does not accept an old restore response after selecting away and back", async () => {
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
        title: "First work order",
        description: null,
        status: "in_progress",
      },
      {
        id: "wo-2",
        code: "WO-002",
        title: "Second work order",
        description: null,
        status: "assigned",
      },
    ];

    const restoring = store.restoreOpenedWorkspace();
    store.selectWorkOrder("wo-2");
    store.selectWorkOrder("wo-1");
    deferred.resolve(workspaceResponse("wo-1", "ev-1"));
    await restoring;

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.workspace).toBeNull();
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("ignores unavailable session storage while reading restore markers", async () => {
    const getItemSpy = vi
      .spyOn(Storage.prototype, "getItem")
      .mockImplementation(() => {
        throw new DOMException("storage unavailable", "SecurityError");
      });
    const removeItemSpy = vi
      .spyOn(Storage.prototype, "removeItem")
      .mockImplementation(() => {
        throw new DOMException("storage unavailable", "SecurityError");
      });

    try {
      const { useWorkOrdersStore } = await import("@/stores/workOrders");
      const store = useWorkOrdersStore();

      await expect(store.restoreOpenedWorkspace()).resolves.toBeUndefined();
      expect(store.selectedWorkOrderId).toBeNull();
      expect(store.workspace).toBeNull();
    } finally {
      getItemSpy.mockRestore();
      removeItemSpy.mockRestore();
    }
  });

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
    expect(store.loadError).toBeNull();
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
    expect(store.openingWorkOrderId).toBeNull();
    expect(store.isOpeningWorkspace).toBe(false);
  });
});
