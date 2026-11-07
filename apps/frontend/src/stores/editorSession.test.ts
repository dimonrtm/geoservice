import { editorTestContext } from "@/test/editorTestContext";
import { useAuthStore } from "./auth";
import * as changeSetApi from "@/api/editVersionChangeSet";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import type { WorkspaceResponse } from "@/contracts/work-orders";

const { fetchAssignedWorkOrdersMock, openEditVersionMock, readMapMock } =
  vi.hoisted(() => ({
    fetchAssignedWorkOrdersMock: vi.fn(),
    openEditVersionMock: vi.fn(),
    readMapMock: vi.fn(),
  }));
const SELECTED_WORK_ORDER_STORAGE_KEY = "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";

vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
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
        draftVersionToken: "1",
        hasPersistedChangeSet: false,
        basicValidation: null,
        changeSet: null,
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

describe("editor version session", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    sessionStorage.clear();
    setActivePinia(createPinia());
    const auth = useAuthStore();
    auth.token = "t";
    auth.user = { id: "actor", email: "a@local", role: "editor" };
  });

  it("restores pending commands even when the published map remains read-only", async () => {
    vi.useFakeTimers();
    const changes = vi
      .spyOn(changeSetApi, "fetchEditVersionChangeSet")
      .mockRejectedValue(networkFailure());
    try {
      const context = editorTestContext();
      const restore = vi
        .spyOn(context.editVersionCommands, "restorePendingSave")
        .mockResolvedValue();
      context.workOrders.selectWorkOrder("wo-1");
      openEditVersionMock.mockResolvedValue(openEditVersionResponse());
      readMapMock.mockResolvedValue(workspaceResponse());
      const opening = context.editorSession.openSelectedWorkOrder();
      await vi.runAllTimersAsync();
      await opening;
      expect(changes).toHaveBeenCalledTimes(5);
      expect(context.editorSession.activeWorkspace?.workOrder.id).toBe("wo-1");
      expect(restore).toHaveBeenCalledOnce();
      expect(context.editor.readyFor("feature-1")).toBe(false);
    } finally {
      changes.mockRestore();
      vi.useRealTimers();
    }
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

    const store = editorTestContext();

    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Assigned work",
        description: "Old user work order",
        status: "assigned",
      },
    ];
    store.workOrders.isLoading = true;
    store.workOrders.loadError = {
      summary: "load failed",
      guidance: null,
      action: null,
      diagnostics: { code: null, correlationId: null },
    };
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse());
    store.editorSession.openingWorkOrderId = "wo-1";
    store.editorSession.openWorkspaceErrorByWorkOrderId = {
      "wo-1": {
        summary: "open failed",
        guidance: null,
        action: null,
        diagnostics: { code: null, correlationId: null },
      },
    };
    store.editorSession.openWorkspaceErrorOperationByWorkOrderId = {
      "wo-1": "open",
    };
    store.editorSession.openWorkspaceRequestSeq = 7;
    store.workOrders.loadAssignedRequestSeq = 11;

    store.workOrders.reset();
    store.editorSession.resetEditor();

    expect(store.workOrders.items).toEqual([]);
    expect(store.workOrders.isLoading).toBe(false);
    expect(store.workOrders.loadError).toBeNull();
    expect(store.workOrders.selectedWorkOrderId).toBeNull();
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.openedEditVersionId).toBeNull();
    expect(store.editor.snapshot).toBeNull();
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
    expect(store.editorSession.openWorkspaceErrorByWorkOrderId).toEqual({});
    expect(
      store.editorSession.openWorkspaceErrorOperationByWorkOrderId,
    ).toEqual({});
    expect(store.editorSession.openWorkspaceRequestSeq).toBe(8);
    expect(store.workOrders.loadAssignedRequestSeq).toBe(12);
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

    const store = editorTestContext();
    store.workOrders.selectedWorkOrderId = "wo-1";
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse());

    store.workOrders.reset({
      preserveOpenedWorkspace: true,
      preserveSelectedWorkOrder: true,
    });
    store.editorSession.resetEditor({
      preserveOpenedWorkspace: true,
      preserveSelectedWorkOrder: true,
    });

    expect(store.workOrders.selectedWorkOrderId).toBeNull();
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.openedEditVersionId).toBeNull();
    expect(store.editor.snapshot).toBeNull();
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
  });

  it("keeps the opened workspace when the same work order is selected again", async () => {
    const store = editorTestContext();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse("wo-1", "ev-1"));
    sessionStorage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );

    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    expect(store.editor.snapshot?.workOrder.id).toBe("wo-1");
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
  });

  it("evicts the client workspace when another work order is selected", async () => {
    const store = editorTestContext();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });
    store.editorSession.openedWorkOrderId = "wo-1";
    store.editorSession.openedEditVersionId = "ev-1";
    store.seed(workspaceResponse("wo-1", "ev-1"));
    sessionStorage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );

    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-2",
    });

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-2");
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.openedEditVersionId).toBeNull();
    expect(store.editor.snapshot).toBeNull();
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-2" }),
    );
  });

  it("tracks the initiating work order while open is pending", async () => {
    const openResponse = openEditVersionResponse("wo-1");
    const openDeferred = createDeferred<typeof openResponse>();
    openEditVersionMock.mockReturnValue(openDeferred.promise);
    readMapMock.mockResolvedValue(workspaceResponse("wo-1", "ev-1"));

    const store = editorTestContext();
    store.workOrders.items = [
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
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    const opening = store.editorSession.openSelectedWorkOrder();

    expect(store.editorSession.openingWorkOrderId).toBe("wo-1");
    expect(store.editorSession.isOpeningWorkspace).toBe(true);

    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-2",
    });
    expect(store.editorSession.openingWorkOrderId).toBe("wo-1");

    openDeferred.resolve(openResponse);
    await opening;

    expect(readMapMock).not.toHaveBeenCalled();
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
  });

  it("opens selected work order and stores workspace", async () => {
    openEditVersionMock.mockResolvedValue(openEditVersionResponse());
    readMapMock.mockResolvedValue(workspaceResponse());

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
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    await store.editorSession.openSelectedWorkOrder();

    expect(openEditVersionMock).toHaveBeenCalledWith("wo-1");
    expect(readMapMock).toHaveBeenCalledWith("wo-1", "ev-1");
    expect(store.workOrders.items[0]?.status).toBe("in_progress");
    expect(store.editorSession.openedWorkOrderId).toBe("wo-1");
    expect(store.editorSession.openedEditVersionId).toBe("ev-1");
    expect(store.editorSession.activeWorkspace?.workOrder.code).toBe("WO-001");
    expect(store.editorSession.activeWorkspaceKey).toBe("wo-1:ev-1");
    expect(store.editorSession.selectedOpenWorkspaceError).toBeNull();
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
  });

  it("maps a missing work order to refresh", async () => {
    openEditVersionMock.mockRejectedValue(
      apiFailure("WORK_ORDER_NOT_FOUND", 404),
    );

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "assigned",
      },
    ];
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    await store.editorSession.openSelectedWorkOrder();

    expect(store.editorSession.selectedOpenWorkspaceError?.action?.id).toBe(
      "refresh",
    );
    expect(
      store.editorSession.selectedOpenWorkspaceError?.diagnostics.correlationId,
    ).toBe("request-id");
    expect(store.editorSession.selectedOpenWorkspaceErrorOperation).toBe(
      "open",
    );
  });

  it("persists opened workspace identifiers after successful open", async () => {
    openEditVersionMock.mockResolvedValue(openEditVersionResponse());
    readMapMock.mockResolvedValue(workspaceResponse());

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
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    await store.editorSession.openSelectedWorkOrder();

    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBe(
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
  });

  it("restores a selected work order without fetching a workspace", async () => {
    sessionStorage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1" }),
    );

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

    await store.editorSession.restoreOpenedWorkspace();

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
    expect(store.editorSession.activeWorkspace).toBeNull();
    expect(openEditVersionMock).not.toHaveBeenCalled();
    expect(readMapMock).not.toHaveBeenCalled();
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

    const store = editorTestContext();
    store.workOrders.items = [
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

    await store.editorSession.restoreOpenedWorkspace();

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-2");
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
    expect(readMapMock).not.toHaveBeenCalled();
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

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Первый наряд",
        description: null,
        status: "in_progress",
      },
    ];

    await store.editorSession.restoreOpenedWorkspace();

    expect(store.workOrders.selectedWorkOrderId).toBeNull();
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBeNull();
    expect(sessionStorage.getItem(OPENED_WORKSPACE_STORAGE_KEY)).toBeNull();
    expect(readMapMock).not.toHaveBeenCalled();
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

      const store = editorTestContext();
      store.workOrders.items = [
        {
          id: "wo-1",
          code: "WO-001",
          title: "Первый наряд",
          description: null,
          status: "assigned",
        },
      ];

      await expect(
        store.editorSession.restoreOpenedWorkspace(),
      ).resolves.toBeUndefined();

      expect(store.workOrders.selectedWorkOrderId).toBeNull();
      expect(
        sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY),
      ).toBeNull();
      expect(readMapMock).not.toHaveBeenCalled();
    },
  );

  it("restores opened workspace from session storage without opening edit version again", async () => {
    sessionStorage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    readMapMock.mockResolvedValue(workspaceResponse("wo-1", "ev-1"));

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: null,
        status: "in_progress",
      },
    ];

    await store.editorSession.restoreOpenedWorkspace();

    expect(openEditVersionMock).not.toHaveBeenCalled();
    expect(readMapMock).toHaveBeenCalledWith("wo-1", "ev-1");
    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
    expect(store.editorSession.openedWorkOrderId).toBe("wo-1");
    expect(store.editorSession.openedEditVersionId).toBe("ev-1");
    expect(store.editorSession.activeWorkspace?.workOrder.code).toBe("WO-001");
    expect(store.editorSession.activeWorkspaceKey).toBe("wo-1:ev-1");
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
  });

  it("clears persisted workspace when saved work order is no longer assigned", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-missing", editVersionId: "ev-1" }),
    );

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

    await store.editorSession.restoreOpenedWorkspace();

    expect(readMapMock).not.toHaveBeenCalled();
    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBeNull();
    expect(store.workOrders.selectedWorkOrderId).toBeNull();
    expect(store.editorSession.activeWorkspace).toBeNull();
  });

  it("clears a stale marker and offers reopen when the edit version disappeared", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    readMapMock.mockRejectedValue(apiFailure("EDIT_VERSION_NOT_FOUND", 404));

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "in_progress",
      },
    ];

    await store.editorSession.restoreOpenedWorkspace();

    expect(sessionStorage.getItem("geoservice:opened-workspace")).toBeNull();
    expect(store.editorSession.selectedOpenWorkspaceError?.action?.id).toBe(
      "reopen",
    );
    expect(store.editorSession.selectedOpenWorkspaceErrorOperation).toBe(
      "restore",
    );
  });

  it("preserves the marker and retries the original restore after a network failure", async () => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    readMapMock.mockRejectedValueOnce(networkFailure());
    readMapMock.mockResolvedValueOnce(workspaceResponse("wo-1", "ev-1"));

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Наряд",
        description: null,
        status: "in_progress",
      },
    ];

    await store.editorSession.restoreOpenedWorkspace();
    await store.editorSession.retrySelectedWorkspaceError();

    expect(openEditVersionMock).not.toHaveBeenCalled();
    expect(readMapMock).toHaveBeenCalledTimes(2);
    expect(store.editorSession.activeWorkspace?.workOrder.id).toBe("wo-1");
  });

  it("keeps action retry available when workspace loading fails after open", async () => {
    openEditVersionMock.mockResolvedValue(openEditVersionResponse());
    readMapMock.mockRejectedValue(networkFailure());

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
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    await store.editorSession.openSelectedWorkOrder();

    expect(store.workOrders.items[0]?.status).toBe("in_progress");
    expect(store.editor.snapshot).toBeNull();
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.selectedOpenWorkspaceError?.action?.id).toBe(
      "retry",
    );
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
  });

  it("does not replace workspace when selection changed during opening", async () => {
    openEditVersionMock.mockResolvedValue(openEditVersionResponse("wo-1"));
    readMapMock.mockResolvedValue(workspaceResponse("wo-1", "ev-1"));

    const store = editorTestContext();
    store.workOrders.items = [
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
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    const opening = store.editorSession.openSelectedWorkOrder();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-2",
    });
    await opening;

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-2");
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.activeWorkspace).toBeNull();
    expect(
      store.editorSession.openWorkspaceErrorByWorkOrderId["wo-1"],
    ).toBeUndefined();
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
    readMapMock.mockReturnValue(deferred.promise);

    const store = editorTestContext();
    store.workOrders.items = [
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

    const restoring = store.editorSession.restoreOpenedWorkspace();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-2",
    });
    deferred.resolve(workspaceResponse("wo-1", "ev-1"));
    await restoring;

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-2");
    expect(store.editor.snapshot).toBeNull();
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
    readMapMock.mockReturnValue(deferred.promise);

    const store = editorTestContext();
    store.workOrders.items = [
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

    const restoring = store.editorSession.restoreOpenedWorkspace();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-2",
    });
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });
    deferred.resolve(workspaceResponse("wo-1", "ev-1"));
    await restoring;

    expect(store.workOrders.selectedWorkOrderId).toBe("wo-1");
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editor.snapshot).toBeNull();
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
      const store = editorTestContext();

      await expect(
        store.editorSession.restoreOpenedWorkspace(),
      ).resolves.toBeUndefined();
      expect(store.workOrders.selectedWorkOrderId).toBeNull();
      expect(store.editor.snapshot).toBeNull();
    } finally {
      getItemSpy.mockRestore();
      removeItemSpy.mockRestore();
    }
  });

  it("ignores open workspace response after reset", async () => {
    const openResponse = openEditVersionResponse();
    const openDeferred = createDeferred<typeof openResponse>();
    openEditVersionMock.mockReturnValue(openDeferred.promise);
    readMapMock.mockResolvedValue(workspaceResponse());

    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Old user work order",
        description: null,
        status: "assigned",
      },
    ];
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "wo-1",
    });

    const opening = store.editorSession.openSelectedWorkOrder();
    expect(store.editorSession.isOpeningWorkspace).toBe(true);

    store.workOrders.reset();
    store.editorSession.resetEditor();
    openDeferred.resolve(openResponse);
    await opening;

    expect(readMapMock).not.toHaveBeenCalled();
    expect(store.workOrders.items).toEqual([]);
    expect(store.editorSession.openedWorkOrderId).toBeNull();
    expect(store.editorSession.openedEditVersionId).toBeNull();
    expect(store.editor.snapshot).toBeNull();
    expect(store.editorSession.openingWorkOrderId).toBeNull();
    expect(store.editorSession.isOpeningWorkspace).toBe(false);
  });
});

vi.mock("@/api/editVersions", () => ({ openEditVersion: openEditVersionMock }));
vi.mock("@/api/editVersionMap", async () => {
  const { fixtureMap } = await import("@/test/editorReadFixtures");
  return {
    fetchEditVersionMap: (workOrderId: string, versionId: string) =>
      fixtureMap(readMapMock, workOrderId, versionId),
  };
});
vi.mock("@/api/editVersionChangeSet", async () => ({
  fetchEditVersionChangeSet: (await import("@/test/editorReadFixtures"))
    .fixtureChangeSet,
}));
vi.mock("@/api/featureBaseline", async () => ({
  fetchFeatureBaseline: (await import("@/test/editorReadFixtures"))
    .fixtureBaseline,
}));
