import { editorTestContext } from "@/test/editorTestContext";
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
  readMap: vi.fn(),
  openEditVersion: vi.fn(),
  saveFeatureGeometry: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
describe("workOrders local editing", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    vi.clearAllMocks();
  });
  it("cancels without API and keeps current independent", () => {
    const store = editorTestContext();
    store.workOrders.items = [
      {
        id: target.workOrderId,
        code: "WO",
        title: "Work",
        description: null,
        status: "in_progress",
      },
    ];
    store.seed(workspaceFixture());
    store.editorSession.openedWorkOrderId =
      store.workOrders.selectedWorkOrderId = target.workOrderId;
    store.editorSession.openedEditVersionId = target.editVersionId;
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      true,
    );
    expect(store.editVersionDraft.moveLocalVertex([65.1, 44.3])).toBe(true);
    expect(store.editVersionDraft.localDraft?.candidateGeometry).not.toEqual(
      store.editor.snapshot!.workOrder.editVersion.features.features[0]
        ?.geometry,
    );
    expect(store.editVersionDraft.cancelLocalEdit()).toBe(true);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
});

function editableStore() {
  const auth = useAuthStore();
  auth.token = "test";
  auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
  const store = editorTestContext();
  store.workOrders.items = [
    {
      id: target.workOrderId,
      code: "WO",
      title: "Work",
      description: null,
      status: "in_progress",
    },
  ];
  store.seed(workspaceFixture());
  store.editorSession.openedWorkOrderId = store.workOrders.selectedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  store.editVersionDraft.beginLocalEdit(target.featureId, 1);
  store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
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
    store.editVersionDraft.cancelLocalEdit();
    store.seed(workspaceFixture(true));
    const baseline =
      store.editor.snapshot!.workOrder.editVersion.changeSet!.baselineGeometry;
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
    api.readMap.mockResolvedValue(workspaceFixture());
    expect(store.editVersionCommands.beginRevert()).toBe("confirm");
    const id = store.editVersionCommands.revertConfirmation!.confirmationId;
    await store.editVersionCommands.confirmRevert(id);
    await settle(store.editVersionCommands);
    await store.editVersionCommands.confirmRevert(id);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(api.saveFeatureGeometry.mock.calls[0]).toEqual([
      target,
      {
        commandId: expect.any(String),
        draftVersionToken: "revision-b",
        geometry: baseline,
      },
    ]);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(store.editVersionCommands.recoveryRecord).toBeNull();
    expect(store.editor.snapshot?.workOrder.editVersion.changeSet).toBeNull();
  });
  it("discard dirty then cancel does not restore candidate", () => {
    const store = editableStore();
    store.seed(workspaceFixture(true));
    const draft = JSON.stringify(store.editVersionDraft.localDraft);
    expect(store.editVersionCommands.beginRevert()).toBe("resolve-dirty");
    store.editVersionCommands.cancelRevert(
      store.editVersionCommands.revertConfirmation!.confirmationId,
    );
    expect(JSON.stringify(store.editVersionDraft.localDraft)).toBe(draft);
    store.editVersionCommands.beginRevert();
    const id = store.editVersionCommands.revertConfirmation!.confirmationId;
    expect(store.editVersionCommands.discardLocalDraftForRevert(id)).toBe(true);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(store.editVersionCommands.revertConfirmation?.phase).toBe("confirm");
    store.editVersionCommands.cancelRevert(id);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it.each(["actor", "token", "workspace", "access"])(
    "invalidates revert confirmation on %s change",
    async (change) => {
      const store = editableStore();
      store.seed(workspaceFixture(true));
      store.editVersionCommands.beginRevert();
      const id = store.editVersionCommands.revertConfirmation!.confirmationId;
      store.editVersionCommands.discardLocalDraftForRevert(id);
      if (change === "actor") useAuthStore().user!.id = "other";
      if (change === "token") {
        const newer = workspaceFixture(true);
        newer.workOrder.editVersion.draftVersionToken = "new";
        store.editor.applyReadback(newer);
      }
      if (change === "workspace")
        store.workOrders.selectedWorkOrderId = "other";
      if (change === "access") useAuthStore().token = null;
      expect(store.editVersionCommands.revertConfirmation).toBeNull();
      await store.editVersionCommands.confirmRevert(id);
      expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    },
  );
  it("confirmation blocks editing, Save, Cancel and navigation even through store", async () => {
    const store = editableStore();
    store.seed(workspaceFixture(true));
    store.editVersionCommands.beginRevert();
    expect(store.editorNavigation.workspaceInteractionLocked).toBe(true);
    expect(store.editVersionDraft.moveLocalVertex([65.1, 44.4])).toBe(false);
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      false,
    );
    expect(store.editVersionDraft.cancelLocalEdit()).toBe(false);
    expect(store.editVersionDraft.discardLocalChangesKeepingSelection()).toBe(
      false,
    );
    expect(store.editorNavigation.allowWorkspaceNavigation()).toBe(false);
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it("revert storage failure prevents PUT", async () => {
    const store = editableStore();
    store.editVersionDraft.cancelLocalEdit();
    store.seed(workspaceFixture(true));
    store.editVersionCommands.beginRevert();
    vi.spyOn(IDBObjectStore.prototype, "add").mockImplementation(() => {
      throw new Error("quota");
    });
    await store.editVersionCommands.confirmRevert(
      store.editVersionCommands.revertConfirmation!.confirmationId,
    );
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editVersionCommands.storageError).not.toBeNull();
    expect(store.editVersionCommands.recoveryRecord).toBeNull();
  });
  it("discards to persisted current while keeping the selected vertex", () => {
    const store = editableStore();
    store.seed(workspaceFixture(true));
    store.editVersionDraft.$patch({ localDraft: null });
    store.editVersionDraft.beginLocalEdit(target.featureId, 1);
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    expect(store.editVersionDraft.discardLocalChangesKeepingSelection()).toBe(
      true,
    );
    expect(store.editVersionDraft.localDraft).toMatchObject({
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
    expect(store.editVersionDraft.localDraft?.candidateGeometry).toEqual(
      store.editVersionDraft.localDraft?.sourceGeometry,
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
    const draft = store.editVersionDraft.localDraft;
    store.editVersionCommands.localPhase = phase;
    expect(store.editVersionDraft.discardLocalChangesKeepingSelection()).toBe(
      false,
    );
    expect(store.editVersionDraft.localDraft).toBe(draft);
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
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    const first = store.editVersionCommands.saveLocalDraft();
    await store.editVersionCommands.saveLocalDraft();
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
    store.seed(workspaceFixture(true));
    store.editVersionDraft.$patch({ localDraft: null });
    store.editVersionDraft.beginLocalEdit(target.featureId, 1);
    store.editVersionDraft.moveLocalVertex([65.1, 44.200000001]);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.didSaveChangeGeometry).toBe(false);
    store.editorSession.clearOpenedWorkspace({ force: true });
    expect(store.editVersionCommands.didSaveChangeGeometry).toBeNull();
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editor.snapshot?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
    expect(store.editVersionCommands.phase).toBe("idle");
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect((await readRecoveryRecord("actor")).kind).toBe("empty");
  });
  it("does not send when recovery write fails", async () => {
    const store = editableStore();
    vi.spyOn(IDBObjectStore.prototype, "add").mockImplementation(() => {
      throw new Error("quota");
    });
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editVersionDraft.localDraft).not.toBeNull();
  });
  it("readback failure keeps known success and retry reads only", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.readMap.mockRejectedValueOnce(new Error("readback"));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.recoveryRecord).toMatchObject({
      result: { commandState: "succeeded" },
    });
    expect(store.editVersionCommands.phase).toBe("reading-current");
    expect(store.editVersionDraft.moveLocalVertex([65, 44])).toBe(false);
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.refreshCurrentWorkspace();
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.recoveryRecord).toMatchObject({
      result: { commandState: "succeeded" },
    });
    expect(store.editVersionCommands.storageError).not.toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
});

afterEach(stopRecovery);

vi.mock("@/api/editVersions", () => api);
vi.mock("@/api/editVersionMap", async () => {
  const { fixtureMap } = await import("@/test/editorReadFixtures");
  return {
    fetchEditVersionMap: (workOrderId: string, versionId: string) =>
      fixtureMap(api.readMap, workOrderId, versionId),
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
