const api = vi.hoisted(() => ({
  fetchWorkspace: vi.fn(),
  openEditVersion: vi.fn(),
  fetchAssignedWorkOrders: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { IDBFactory } from "fake-indexeddb";
import { workspaceFixture, target } from "@/test/workspaceEditFixture";
import { useWorkOrdersStore } from "./workOrders";
import { useAuthStore } from "./auth";
import { recoveryKey } from "@/contracts/workspace-recovery";
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
  const store = useWorkOrdersStore();
  const ctx = {
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  };
  const older = store.reserveWorkspaceRead(ctx),
    newer = store.reserveWorkspaceRead(ctx);
  expect(store.applyWorkspaceRead(newer, workspaceFixture(true))).toBe(
    "applied",
  );
  expect(store.applyWorkspaceRead(older, workspaceFixture())).toBe(
    "superseded",
  );
  expect(
    store.snapshots[recoveryKey(ctx)]?.workOrder.editVersion.draftVersionToken,
  ).toBe("revision-b");
});
it("readback A updates only A while selected B keeps its workspace and draft", () => {
  const store = useWorkOrdersStore();
  const b = workspaceFixture();
  b.workOrder.id = "B";
  b.workOrder.editVersion.id = "ev-B";
  store.workspace = b;
  store.openedWorkOrderId = store.selectedWorkOrderId = "B";
  store.openedEditVersionId = "ev-B";
  store.beginLocalEdit(target.featureId, 1);
  store.moveLocalVertex([65.1, 44.3]);
  const ctx = {
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  };
  store.applyWorkspaceRead(
    store.reserveWorkspaceRead(ctx),
    workspaceFixture(true),
  );
  expect(store.activeWorkspace?.workOrder.id).toBe("B");
  expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([
    65.1, 44.3,
  ]);
});

it("recovery accepted during ordinary opening still opens the newest workspace", async () => {
  const s = useWorkOrdersStore();
  s.selectedWorkOrderId = target.workOrderId;
  api.openEditVersion.mockResolvedValue({
    editVersion: { id: target.editVersionId },
  });
  let resolve!: (w: ReturnType<typeof workspaceFixture>) => void;
  api.fetchWorkspace.mockReturnValue(
    new Promise((r) => {
      resolve = r;
    }),
  );
  const opening = s.openSelectedWorkOrder();
  await vi.waitFor(() => expect(api.fetchWorkspace).toHaveBeenCalled());
  const newer = s.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  s.applyWorkspaceRead(newer, workspaceFixture(true));
  resolve(workspaceFixture());
  await opening;
  expect(s.activeWorkspace?.workOrder.editVersion.draftVersionToken).toBe(
    "revision-b",
  );
});
it("temporary assignment list failure preserves last confirmed access", async () => {
  const s = useWorkOrdersStore();
  s.items = [
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
  await s.loadAssigned();
  expect(s.items.map((w) => w.id)).toEqual([target.workOrderId]);
  expect(s.loadError).not.toBeNull();
});

it("new recovery GET finishing after superseded ordinary GET still opens workspace", async () => {
  const s = useWorkOrdersStore();
  s.selectedWorkOrderId = target.workOrderId;
  api.openEditVersion.mockResolvedValue({
    editVersion: { id: target.editVersionId },
  });
  let resolve!: (w: ReturnType<typeof workspaceFixture>) => void;
  api.fetchWorkspace.mockReturnValue(
    new Promise((r) => {
      resolve = r;
    }),
  );
  const opening = s.openSelectedWorkOrder();
  await vi.waitFor(() =>
    expect(s.openingEditVersionId).toBe(target.editVersionId),
  );
  const newer = s.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  resolve(workspaceFixture());
  await opening;
  s.applyWorkspaceRead(newer, workspaceFixture(true));
  expect(s.activeWorkspace?.workOrder.editVersion.draftVersionToken).toBe(
    "revision-b",
  );
});
it("obsolete ordinary restore error cannot close newer accepted recovery workspace", async () => {
  const s = useWorkOrdersStore();
  s.selectedWorkOrderId = target.workOrderId;
  s.items = [
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
  api.fetchWorkspace.mockReturnValue(
    new Promise((_r, j) => {
      reject = j;
    }),
  );
  const opening = s.restoreOpenedWorkspace();
  await vi.waitFor(() =>
    expect(s.openingEditVersionId).toBe(target.editVersionId),
  );
  const newer = s.reserveWorkspaceRead({
    actorId: "actor",
    workOrderId: target.workOrderId,
    editVersionId: target.editVersionId,
  });
  s.applyWorkspaceRead(newer, workspaceFixture(true));
  reject(new Error("old failure"));
  await opening;
  expect(s.activeWorkspace?.workOrder.editVersion.draftVersionToken).toBe(
    "revision-b",
  );
});
