import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  workspaceFixture,
  target,
  successFixture,
} from "@/test/workspaceEditFixture";
const api = vi.hoisted(() => ({
  saveFeatureGeometry: vi.fn(),
  fetchWorkspace: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { useWorkOrdersStore } from "./workOrders";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
function setup() {
  const auth = useAuthStore();
  auth.token = "t";
  auth.user = { id: "actor", email: "a@local", role: "editor" };
  const s = useWorkOrdersStore();
  s.workspace = workspaceFixture();
  s.selectedWorkOrderId = s.openedWorkOrderId = target.workOrderId;
  s.openedEditVersionId = target.editVersionId;
  s.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
    { id: "B", code: "B", title: "B", description: null, status: "assigned" },
  ];
  s.beginLocalEdit(target.featureId, 1);
  s.moveLocalVertex([65.1, 44.2]);
  return s;
}
beforeEach(() => {
  setActivePinia(createPinia());
  sessionStorage.clear();
  vi.resetAllMocks();
});
it("discard leaves without HTTP, stay preserves draft, old confirmation is inert", async () => {
  const s = setup();
  const id = s.requestNavigation({ kind: "work-order", workOrderId: "B" })!;
  await s.resolveNavigation(id, "stay");
  expect(s.localDraft).not.toBeNull();
  await s.resolveNavigation(id, "discard");
  expect(s.selectedWorkOrderId).toBe(target.workOrderId);
  await s.resolveNavigation(
    s.requestNavigation({ kind: "work-order", workOrderId: "B" })!,
    "discard",
  );
  expect(s.selectedWorkOrderId).toBe("B");
  expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
});
it("save and leave follows original target only after success and current GET", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockImplementation(async (_t, r) =>
    successFixture(r.commandId),
  );
  api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
  const id = s.requestNavigation({ kind: "work-order", workOrderId: "B" })!;
  await s.resolveNavigation(id, "save");
  await vi.waitFor(() => expect(s.selectedWorkOrderId).toBe("B"));
  expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  await s.resolveNavigation(id, "save");
  expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
});
it("unknown cancels navigation forever even after eventual success", async () => {
  const s = setup();
  api.saveFeatureGeometry
    .mockRejectedValueOnce({ isAxiosError: true, request: {} })
    .mockImplementation(async (_t, r) => successFixture(r.commandId));
  api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
  await s.resolveNavigation(
    s.requestNavigation({ kind: "work-order", workOrderId: "B" })!,
    "save",
  );
  await vi.waitFor(() => expect(s.commandResult).not.toBeNull());
  expect(s.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.navigation).toBeNull();
  useWorkspaceRecoveryStore().stopRuntime();
});

it("logout resolves dirty selected draft even when another workspace has stale material", () => {
  const s = setup();
  s.staleComparisons.other = {
    source: null,
    candidate: workspaceFixture().workOrder.editVersion.features.features[0]!
      .geometry as import("@/contracts/workspace-edit").LineStringXY,
    commandId: "old",
    featureId: "old",
  };
  s.requestNavigation({ kind: "logout" });
  expect(s.navigation?.phase).toBe("dirty");
});
it("storage failure cancels save-and-leave and releases the dialog", async () => {
  const s = setup();
  Object.defineProperty(globalThis, "indexedDB", {
    value: undefined,
    configurable: true,
  });
  await s.resolveNavigation(
    s.requestNavigation({ kind: "work-order", workOrderId: "B" })!,
    "save",
  );
  expect(s.navigation).toBeNull();
  expect(s.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.localDraft).not.toBeNull();
});
it("protocol failure cancels save-and-leave and releases the dialog", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockResolvedValue({ commandId: "wrong" });
  await s.resolveNavigation(
    s.requestNavigation({ kind: "work-order", workOrderId: "B" })!,
    "save",
  );
  await vi.waitFor(() => expect(s.phase).toBe("blocked"));
  expect(s.navigation).toBeNull();
  expect(s.selectedWorkOrderId).toBe(target.workOrderId);
});

it("GET failure permanently cancels logout even after successful manual readback", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockImplementation(async (_t, r) =>
    successFixture(r.commandId),
  );
  api.fetchWorkspace
    .mockRejectedValueOnce({ isAxiosError: true, request: {} })
    .mockResolvedValue(workspaceFixture(true));
  await s.resolveNavigation(s.requestNavigation({ kind: "logout" })!, "save");
  await vi.waitFor(() => expect(s.readbackError).not.toBeNull());
  expect(s.navigation).toBeNull();
  const recovery = useWorkspaceRecoveryStore();
  const key = Object.keys(recovery.records)[0]!;
  await recovery.retryRead(key);
  await vi.waitFor(() => expect(Object.keys(recovery.records)).toHaveLength(0));
  expect(useAuthStore().user?.id).toBe("actor");
  expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
});

it("domain rejection cancels save-and-leave and retains the editable attempt", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockRejectedValue({
    isAxiosError: true,
    response: {
      status: 422,
      data: { code: "GEOMETRY_INVALID", message: "invalid" },
    },
  });
  await s.resolveNavigation(
    s.requestNavigation({ kind: "work-order", workOrderId: "B" })!,
    "save",
  );
  await vi.waitFor(() => expect(s.navigation).toBeNull());
  expect(s.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.localDraft).not.toBeNull();
  expect(api.fetchWorkspace).not.toHaveBeenCalled();
});
