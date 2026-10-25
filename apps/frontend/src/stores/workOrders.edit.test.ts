import {
  settle,
  readPersisted as readRecoveryRecord,
  stopRecovery,
} from "@/test/recoveryIntegration";
import { IDBObjectStore } from "fake-indexeddb";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  workspaceFixture,
  target,
  successFixture,
} from "@/test/workspaceEditFixture";
import { useAuthStore } from "./auth";

const api = vi.hoisted(() => ({
  fetchAssignedWorkOrders: vi.fn(),
  fetchWorkspace: vi.fn(),
  openEditVersion: vi.fn(),
  saveFeatureGeometry: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { useWorkOrdersStore } from "./workOrders";
describe("workOrders local editing", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    vi.clearAllMocks();
  });
  it("cancels without API and keeps current independent", () => {
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: target.workOrderId,
        code: "WO",
        title: "Work",
        description: null,
        status: "in_progress",
      },
    ];
    store.workspace = workspaceFixture();
    store.openedWorkOrderId = store.selectedWorkOrderId = target.workOrderId;
    store.openedEditVersionId = target.editVersionId;
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(true);
    expect(store.moveLocalVertex([65.1, 44.3])).toBe(true);
    expect(store.localDraft?.candidateGeometry).not.toEqual(
      store.workspace.workOrder.editVersion.features.features[0]?.geometry,
    );
    expect(store.cancelLocalEdit()).toBe(true);
    expect(store.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
});

function editableStore() {
  const auth = useAuthStore();
  auth.token = "test";
  auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
  const store = useWorkOrdersStore();
  store.items = [
    {
      id: target.workOrderId,
      code: "WO",
      title: "Work",
      description: null,
      status: "in_progress",
    },
  ];
  store.workspace = workspaceFixture();
  store.openedWorkOrderId = store.selectedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  store.beginLocalEdit(target.featureId, 1);
  store.moveLocalVertex([65.1, 44.2]);
  return store;
}
describe("Save orchestration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetAllMocks();
    sessionStorage.clear();
    setActivePinia(createPinia());
  });
  it("revert uses change set baseline without selection and persists before PUT", async () => {
    const store = editableStore();
    store.cancelLocalEdit();
    store.workspace = workspaceFixture(true);
    const baseline =
      store.workspace.workOrder.editVersion.changeSet!.baselineGeometry;
    api.saveFeatureGeometry.mockImplementation(async (_t, request) => {
      expect((await readRecoveryRecord("actor")).kind).toBe("record");
      return Promise.resolve({
        ...successFixture(request.commandId),
        operation: "unchanged",
        hasPersistedChangeSet: false,
        basicValidation: null,
        updatedFeature: { id: target.featureId, geometry: baseline },
      });
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture());
    expect(store.beginRevert()).toBe("confirm");
    const id = store.revertConfirmation!.confirmationId;
    await store.confirmRevert(id);
    await settle(store);
    await store.confirmRevert(id);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(api.saveFeatureGeometry.mock.calls[0]).toEqual([
      target,
      {
        commandId: expect.any(String),
        draftVersionToken: "revision-b",
        geometry: baseline,
      },
    ]);
    expect(store.localDraft).toBeNull();
    expect(store.recoveryRecord).toBeNull();
    expect(store.workspace?.workOrder.editVersion.changeSet).toBeNull();
  });
  it("discard dirty then cancel does not restore candidate", () => {
    const store = editableStore();
    store.workspace = workspaceFixture(true);
    const draft = JSON.stringify(store.localDraft);
    expect(store.beginRevert()).toBe("resolve-dirty");
    store.cancelRevert(store.revertConfirmation!.confirmationId);
    expect(JSON.stringify(store.localDraft)).toBe(draft);
    store.beginRevert();
    const id = store.revertConfirmation!.confirmationId;
    expect(store.discardLocalDraftForRevert(id)).toBe(true);
    expect(store.localDraft).toBeNull();
    expect(store.revertConfirmation?.phase).toBe("confirm");
    store.cancelRevert(id);
    expect(store.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it.each(["actor", "token", "workspace", "access"])(
    "invalidates revert confirmation on %s change",
    async (change) => {
      const store = editableStore();
      store.workspace = workspaceFixture(true);
      store.beginRevert();
      const id = store.revertConfirmation!.confirmationId;
      store.discardLocalDraftForRevert(id);
      if (change === "actor") useAuthStore().user!.id = "other";
      if (change === "token")
        store.workspace.workOrder.editVersion.draftVersionToken = "new";
      if (change === "workspace") store.selectedWorkOrderId = "other";
      if (change === "access") useAuthStore().token = null;
      expect(store.revertConfirmation).toBeNull();
      await store.confirmRevert(id);
      expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    },
  );
  it("confirmation blocks editing, Save, Cancel and navigation even through store", async () => {
    const store = editableStore();
    store.workspace = workspaceFixture(true);
    store.beginRevert();
    expect(store.workspaceInteractionLocked).toBe(true);
    expect(store.moveLocalVertex([65.1, 44.4])).toBe(false);
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(false);
    expect(store.cancelLocalEdit()).toBe(false);
    expect(store.discardLocalChangesKeepingSelection()).toBe(false);
    expect(store.allowWorkspaceNavigation()).toBe(false);
    await store.saveLocalDraft();
    await settle(store);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it("revert storage failure prevents PUT", async () => {
    const store = editableStore();
    store.cancelLocalEdit();
    store.workspace = workspaceFixture(true);
    store.beginRevert();
    vi.spyOn(IDBObjectStore.prototype, "add").mockImplementation(() => {
      throw new Error("quota");
    });
    await store.confirmRevert(store.revertConfirmation!.confirmationId);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.storageError).not.toBeNull();
    expect(store.recoveryRecord).toBeNull();
  });
  it("discards to persisted current while keeping the selected vertex", () => {
    const store = editableStore();
    store.workspace = workspaceFixture(true);
    store.$patch({ localDraft: null });
    store.beginLocalEdit(target.featureId, 1);
    store.moveLocalVertex([65.1, 44.3]);
    expect(store.discardLocalChangesKeepingSelection()).toBe(true);
    expect(store.localDraft).toMatchObject({
      featureId: target.featureId,
      vertexIndex: 1,
      sourceToken: "revision-b",
      candidateGeometry: {
        coordinates: [
          [65, 44],
          [65.1, 44.2],
          [65.2, 44],
        ],
      },
    });
    expect(store.localDraft?.candidateGeometry).toEqual(
      store.localDraft?.sourceGeometry,
    );
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it.each([
    "stale",
    "sending",
    "unknown",
    "reading-current",
    "blocked",
  ] as const)("refuses discard during %s", (phase) => {
    const store = editableStore();
    const draft = store.localDraft;
    store.localPhase = phase;
    expect(store.discardLocalChangesKeepingSelection()).toBe(false);
    expect(store.localDraft).toBe(draft);
  });
  it("does not resubmit the rejected candidate until it is corrected", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 422,
        data: {
          code: "GEOMETRY_INVALID",
          message: "invalid",
          correlationId: null,
        },
      },
    });
    await store.saveLocalDraft();
    await settle(store);
    await store.saveLocalDraft();
    await settle(store);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    store.moveLocalVertex([65.1, 44.3]);
    await store.saveLocalDraft();
    await settle(store);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(2);
  });
  it("starts one request for concurrent Save calls", async () => {
    const store = editableStore();
    let resolve!: (value: ReturnType<typeof successFixture>) => void;
    api.saveFeatureGeometry.mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    const first = store.saveLocalDraft();
    await store.saveLocalDraft();
    await vi.waitFor(() =>
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1),
    );
    resolve(
      successFixture(api.saveFeatureGeometry.mock.calls[0]![1].commandId),
    );
    await first;
  });
  it("classifies canonical no-op against submitted current rather than baseline", async () => {
    const store = editableStore();
    store.workspace = workspaceFixture(true);
    store.$patch({ localDraft: null });
    store.beginLocalEdit(target.featureId, 1);
    store.moveLocalVertex([65.1, 44.200000001]);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    expect(store.didSaveChangeGeometry).toBe(false);
    store.clearOpenedWorkspace({ force: true });
    expect(store.didSaveChangeGeometry).toBeNull();
  });
  it("writes before PUT and reads canonical current after success", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation(async (_target, request) => {
      expect(await readRecoveryRecord("actor")).toMatchObject({
        kind: "record",
        record: { state: "unknown", command: { request } },
      });
      return Promise.resolve(successFixture(request.commandId));
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    expect(store.workspace?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
    expect(store.phase).toBe("idle");
    expect(store.localDraft).toBeNull();
    expect((await readRecoveryRecord("actor")).kind).toBe("empty");
  });
  it("does not send when recovery write fails", async () => {
    const store = editableStore();
    vi.spyOn(IDBObjectStore.prototype, "add").mockImplementation(() => {
      throw new Error("quota");
    });
    await store.saveLocalDraft();
    await settle(store);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.localDraft).not.toBeNull();
  });
  it("readback failure keeps known success and retry reads only", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockRejectedValueOnce(new Error("readback"));
    await store.saveLocalDraft();
    await settle(store);
    expect(store.recoveryRecord).toMatchObject({
      result: { commandState: "succeeded" },
    });
    expect(store.phase).toBe("reading-current");
    expect(store.moveLocalVertex([65, 44])).toBe(false);
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.refreshCurrentWorkspace();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("success storage failure blocks next mutation without losing result", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation((_t, r) => {
      vi.spyOn(IDBObjectStore.prototype, "put").mockImplementation(() => {
        throw new Error("quota");
      });
      return Promise.resolve(successFixture(r.commandId));
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    await store.saveLocalDraft();
    await settle(store);
    expect(store.recoveryRecord).toMatchObject({
      result: { commandState: "succeeded" },
    });
    expect(store.storageError).not.toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
});

afterEach(stopRecovery);
