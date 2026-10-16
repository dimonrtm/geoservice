import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  workspaceFixture,
  target,
  successFixture,
} from "@/test/workspaceEditFixture";
import { useAuthStore } from "./auth";
import { readRecoveryRecord } from "./workspaceRecoveryStorage";
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
  it("writes before PUT and reads canonical current after success", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation((_target, request) => {
      expect(readRecoveryRecord("actor")).toMatchObject({
        kind: "record",
        record: { state: "unknown", command: { request } },
      });
      return Promise.resolve(successFixture(request.commandId));
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    expect(store.workspace?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
    expect(store.phase).toBe("idle");
    expect(store.localDraft).toBeNull();
    expect(readRecoveryRecord("actor").kind).toBe("empty");
  });
  it("does not send when recovery write fails", async () => {
    const store = editableStore();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    await store.saveLocalDraft();
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
    expect(store.commandResult?.commandState).toBe("succeeded");
    expect(store.phase).toBe("reading-current");
    expect(store.moveLocalVertex([65, 44])).toBe(false);
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.refreshCurrentWorkspace();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("success storage failure blocks next mutation without losing result", async () => {
    const store = editableStore();
    api.saveFeatureGeometry.mockImplementation((_t, r) => {
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new Error("quota");
      });
      return Promise.resolve(successFixture(r.commandId));
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await store.saveLocalDraft();
    expect(store.commandResult?.commandState).toBe("succeeded");
    expect(store.storageError).not.toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
});
