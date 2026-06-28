import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import type { WorkspaceResponse } from "@/contracts/work-orders";

const fetchAssignedWorkOrdersMock = vi.fn();
const openEditVersionMock = vi.fn();
const fetchWorkspaceMock = vi.fn();

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
    expect(store.items[0]).toMatchObject({ code: "WO-001" });
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBeNull();
  });

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
    expect(store.isOpeningWorkspace).toBe(false);
  });

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

    expect(store.items[0]?.status).toBe("in_progress");
    expect(store.workspace).toBeNull();
    expect(store.openedWorkOrderId).toBeNull();
    expect(store.selectedOpenWorkspaceError).toBe(
      "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
    );
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
});
