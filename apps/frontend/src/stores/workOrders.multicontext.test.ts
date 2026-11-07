import { editorTestContext } from "@/test/editorTestContext";
const api = vi.hoisted(() => ({
  readMap: vi.fn(),
  openEditVersion: vi.fn(),
  fetchAssignedWorkOrders: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { IDBFactory } from "fake-indexeddb";
import { workspaceFixture, target } from "@/test/workspaceEditFixture";
import { useAuthStore } from "./auth";

beforeEach(() => {
  setActivePinia(createPinia());
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  sessionStorage.clear();
  const auth = useAuthStore();
  auth.token = "token";
  auth.user = { id: "actor", email: "a@example.local", role: "editor" };
});
it("a newer ordinary GET prevents an older recovery GET replacing current", () => {
  const store = editorTestContext();
  const ctx = {
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  };
  store.workOrders.selectedWorkOrderId = store.editorSession.openedWorkOrderId =
    ctx.workOrderId;
  store.editorSession.openedEditVersionId = ctx.editVersionId;
  const older = store.editorSession.reserveWorkspaceRead(ctx),
    newer = store.editorSession.reserveWorkspaceRead(ctx);
  expect(
    store.editorSession.applyWorkspaceRead(newer, workspaceFixture(true)),
  ).toBe("applied");
  expect(
    store.editorSession.applyWorkspaceRead(older, workspaceFixture()),
  ).toBe("superseded");
  expect(
    store.editorSession.activeWorkspace?.workOrder.editVersion
      .draftVersionToken,
  ).toBe("revision-b");
});
it("readback A updates only A while selected B keeps its workspace and draft", () => {
  const store = editorTestContext();
  const b = workspaceFixture();
  b.workOrder.id = "B";
  b.workOrder.editVersion.id = "ev-B";
  store.seed(b);
  store.editorSession.openedWorkOrderId = store.workOrders.selectedWorkOrderId =
    "B";
  store.editorSession.openedEditVersionId = "ev-B";
  store.editVersionDraft.beginLocalEdit(target.featureId, 1);
  store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
  const ctx = {
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  };
  store.editorSession.applyWorkspaceRead(
    store.editorSession.reserveWorkspaceRead(ctx),
    workspaceFixture(true),
  );
  expect(store.editorSession.activeWorkspace?.workOrder.id).toBe("B");
  expect(
    store.editVersionDraft.localDraft?.candidateGeometry.coordinates[1],
  ).toEqual([65.1, 44.3]);
});

it("recovery accepted during ordinary opening still opens the newest workspace", async () => {
  const s = editorTestContext();
  s.workOrders.selectedWorkOrderId = target.workOrderId;
  api.openEditVersion.mockResolvedValue({
    editVersion: { id: target.editVersionId },
  });
  let resolve!: (w: ReturnType<typeof workspaceFixture>) => void;
  api.readMap.mockReturnValue(
    new Promise((r) => {
      resolve = r;
    }),
  );
  const opening = s.editorSession.openSelectedWorkOrder();
  await vi.waitFor(() => expect(api.readMap).toHaveBeenCalled());
  const newer = s.editorSession.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  s.editorSession.applyWorkspaceRead(newer, workspaceFixture(true));
  resolve(workspaceFixture());
  await opening;
  expect(
    s.editorSession.activeWorkspace?.workOrder.editVersion.draftVersionToken,
  ).toBe("revision-b");
});
it("temporary assignment list failure preserves last confirmed access", async () => {
  const s = editorTestContext();
  s.workOrders.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
  ];
  api.fetchAssignedWorkOrders.mockRejectedValue({
    isAxiosError: true,
    request: {},
  });
  await s.workOrders.loadAssigned();
  expect(s.workOrders.items.map((w) => w.id)).toEqual([target.workOrderId]);
  expect(s.workOrders.loadError).not.toBeNull();
});

it("new recovery GET finishing after superseded ordinary GET still opens workspace", async () => {
  const s = editorTestContext();
  s.workOrders.selectedWorkOrderId = target.workOrderId;
  api.openEditVersion.mockResolvedValue({
    editVersion: { id: target.editVersionId },
  });
  let resolve!: (w: ReturnType<typeof workspaceFixture>) => void;
  api.readMap.mockReturnValue(
    new Promise((r) => {
      resolve = r;
    }),
  );
  const opening = s.editorSession.openSelectedWorkOrder();
  await vi.waitFor(() =>
    expect(s.editorSession.openingEditVersionId).toBe(target.editVersionId),
  );
  const newer = s.editorSession.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  resolve(workspaceFixture());
  await opening;
  s.editorSession.applyWorkspaceRead(newer, workspaceFixture(true));
  expect(
    s.editorSession.activeWorkspace?.workOrder.editVersion.draftVersionToken,
  ).toBe("revision-b");
});
it("obsolete ordinary restore error cannot close newer accepted recovery workspace", async () => {
  const s = editorTestContext();
  s.workOrders.selectedWorkOrderId = target.workOrderId;
  s.workOrders.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
  ];
  sessionStorage.setItem("geoservice:opened-workspace", JSON.stringify(target));
  let reject!: (error: unknown) => void;
  api.readMap.mockReturnValue(
    new Promise((_r, j) => {
      reject = j;
    }),
  );
  const opening = s.editorSession.restoreOpenedWorkspace();
  await vi.waitFor(() =>
    expect(s.editorSession.openingEditVersionId).toBe(target.editVersionId),
  );
  const newer = s.editorSession.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  s.editorSession.applyWorkspaceRead(newer, workspaceFixture(true));
  reject(new Error("old failure"));
  await opening;
  expect(
    s.editorSession.activeWorkspace?.workOrder.editVersion.draftVersionToken,
  ).toBe("revision-b");
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
