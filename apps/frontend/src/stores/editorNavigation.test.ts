import { editorTestContext } from "@/test/editorTestContext";
import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  workspaceFixture,
  target,
  successFixture,
} from "@/test/workspaceEditFixture";
const api = vi.hoisted(() => ({
  saveFeatureGeometry: vi.fn(),
  readMap: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
function setup() {
  const auth = useAuthStore();
  auth.token = "t";
  auth.user = { id: "actor", email: "a@local", role: "editor" };
  const s = editorTestContext();
  s.seed(workspaceFixture());
  s.workOrders.selectedWorkOrderId = s.editorSession.openedWorkOrderId =
    target.workOrderId;
  s.editorSession.openedEditVersionId = target.editVersionId;
  s.workOrders.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
    { id: "B", code: "B", title: "B", description: null, status: "assigned" },
  ];
  s.editVersionDraft.beginLocalEdit(target.featureId, 1);
  s.editVersionDraft.moveLocalVertex([65.1, 44.2]);
  return s;
}
beforeEach(() => {
  setActivePinia(createPinia());
  sessionStorage.clear();
  vi.resetAllMocks();
});
it("discard leaves without HTTP, stay preserves draft, old confirmation is inert", async () => {
  const s = setup();
  const id = s.editorNavigation.requestNavigation({
    kind: "work-order",
    workOrderId: "B",
  })!;
  await s.editorNavigation.resolveNavigation(id, "stay");
  expect(s.editVersionDraft.localDraft).not.toBeNull();
  await s.editorNavigation.resolveNavigation(id, "discard");
  expect(s.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "B",
    })!,
    "discard",
  );
  expect(s.workOrders.selectedWorkOrderId).toBe("B");
  expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
});
it("save and leave follows original target only after success and current GET", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockImplementation(async (_t, r) =>
    successFixture(r.commandId),
  );
  api.readMap.mockResolvedValue(workspaceFixture(true));
  const id = s.editorNavigation.requestNavigation({
    kind: "work-order",
    workOrderId: "B",
  })!;
  await s.editorNavigation.resolveNavigation(id, "save");
  await vi.waitFor(() => expect(s.workOrders.selectedWorkOrderId).toBe("B"));
  expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  await s.editorNavigation.resolveNavigation(id, "save");
  expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
});
it("unknown cancels navigation forever even after eventual success", async () => {
  const s = setup();
  api.saveFeatureGeometry
    .mockRejectedValueOnce({ isAxiosError: true, request: {} })
    .mockImplementation(async (_t, r) => successFixture(r.commandId));
  api.readMap.mockResolvedValue(workspaceFixture(true));
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "B",
    })!,
    "save",
  );
  await vi.waitFor(() =>
    expect(s.editVersionCommands.commandResult).not.toBeNull(),
  );
  expect(s.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.editorNavigation.navigation).toBeNull();
  useWorkspaceRecoveryStore().stopRuntime();
});

it("logout resolves dirty selected draft even when another workspace has stale material", () => {
  const s = setup();
  s.editVersionCommands.staleComparisons.other = {
    source: null,
    candidate: workspaceFixture().workOrder.editVersion.features.features[0]!
      .geometry as import("@/contracts/workspace-edit").LineStringXY,
    commandId: "old",
    featureId: "old",
  };
  s.editorNavigation.requestNavigation({ kind: "logout" });
  expect(s.editorNavigation.navigation?.phase).toBe("dirty");
});
it("storage failure cancels save-and-leave and releases the dialog", async () => {
  const s = setup();
  Object.defineProperty(globalThis, "indexedDB", {
    value: undefined,
    configurable: true,
  });
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "B",
    })!,
    "save",
  );
  expect(s.editorNavigation.navigation).toBeNull();
  expect(s.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.editVersionDraft.localDraft).not.toBeNull();
});
it("protocol failure cancels save-and-leave and releases the dialog", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockResolvedValue({ commandId: "wrong" });
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "B",
    })!,
    "save",
  );
  await vi.waitFor(() => expect(s.editVersionCommands.phase).toBe("blocked"));
  expect(s.editorNavigation.navigation).toBeNull();
  expect(s.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
});

it("GET failure permanently cancels logout even after successful manual readback", async () => {
  const s = setup();
  api.saveFeatureGeometry.mockImplementation(async (_t, r) =>
    successFixture(r.commandId),
  );
  api.readMap
    .mockRejectedValueOnce({ isAxiosError: true, request: {} })
    .mockResolvedValue(workspaceFixture(true));
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({ kind: "logout" })!,
    "save",
  );
  await vi.waitFor(() =>
    expect(s.editVersionCommands.readbackError).not.toBeNull(),
  );
  expect(s.editorNavigation.navigation).toBeNull();
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
  await s.editorNavigation.resolveNavigation(
    s.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "B",
    })!,
    "save",
  );
  await vi.waitFor(() => expect(s.editorNavigation.navigation).toBeNull());
  expect(s.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
  expect(s.editVersionDraft.localDraft).not.toBeNull();
  expect(api.readMap).not.toHaveBeenCalled();
});

it("logout preparation cannot revoke a replacement session", async () => {
  const s = setup();
  const auth = useAuthStore();
  auth.sessionId = "sid-a";
  let prepared!: (ready: boolean) => void;
  vi.spyOn(useWorkspaceRecoveryStore(), "prepareActorLogout").mockReturnValue(
    new Promise<boolean>((resolve) => (prepared = resolve)),
  );
  const logout = vi.spyOn(auth, "logout");
  const leaving = s.editorNavigation.performNavigation({ kind: "logout" });
  auth.setAuth(
    "new",
    { id: "actor", email: "a@local", role: "editor" },
    { sessionId: "sid-b" },
  );
  s.seed(workspaceFixture());
  s.workOrders.selectedWorkOrderId = s.editorSession.openedWorkOrderId =
    target.workOrderId;
  s.editorSession.openedEditVersionId = target.editVersionId;
  prepared(true);
  await leaving;
  expect(logout).not.toHaveBeenCalled();
  expect(auth.sessionId).toBe("sid-b");
  expect(s.editorSession.activeWorkspace).not.toBeNull();
  logout.mockRestore();
});

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
