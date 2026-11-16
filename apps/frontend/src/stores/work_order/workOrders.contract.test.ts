import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { IDBFactory } from "fake-indexeddb";
import { editorTestContext } from "@/test/editorTestContext";
import { workspaceFixture } from "@/test/workspaceEditFixture";
import { useAuthStore } from "../auth";
const http = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock("@/api/http", () => ({ http }));
const id = "aaaaaaaa-1111-4111-8111-111111111111";
const order = {
  id,
  code: "WO-1",
  title: "Наряд",
  description: null,
  status: "assigned",
};
beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
  sessionStorage.clear();
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  const auth = useAuthStore();
  auth.token = "token";
  auth.user = { id: "actor", email: "a@example.local", role: "editor" };
});
function opened() {
  const context = editorTestContext();
  const workspace = workspaceFixture();
  workspace.workOrder.id = id;
  context.seed(workspace);
  context.workOrders.selectWorkOrder(id);
  context.editorSession.openedWorkOrderId = id;
  context.editorSession.openedEditVersionId = "ev-1";
  context.editVersionDraft.beginLocalEdit("line-1", 1);
  return context;
}
it("keeps every row and reports field issues without a list error", async () => {
  http.get.mockResolvedValue({
    data: { workOrders: [{ ...order, status: 7 }, null] },
  });
  const { workOrders } = editorTestContext();
  await workOrders.loadAssigned();
  expect(workOrders.items).toHaveLength(2);
  expect(workOrders.loadError).toBeNull();
  expect(workOrders.items[0]?.status).toBeNull();
  expect(workOrders.items[0]?.issues.map((issue) => issue.field)).toEqual([
    "status",
  ]);
  workOrders.selectWorkOrder(id);
  expect(workOrders.selectedWorkOrder?.id).toBe(id);
  workOrders.updateWorkOrderStatus(id, "in_progress");
  expect(workOrders.selectedWorkOrder?.issues).toHaveLength(1);
  http.get.mockResolvedValue({ data: { workOrders: [order] } });
  await workOrders.loadAssigned();
  expect(workOrders.selectedWorkOrder?.issues).toEqual([]);
});
it("preserves workspace and draft on unusable envelope without offering retry", async () => {
  const context = opened();
  http.get.mockResolvedValue({ data: { workOrders: [order] } });
  await context.workOrders.loadAssigned();
  const draft = context.editVersionDraft.localDraft;
  http.get.mockResolvedValue({ data: { workOrders: null } });
  await context.workOrders.loadAssigned();
  await context.editorSession.reconcileAssignments();
  expect(context.workOrders.items).toHaveLength(1);
  expect(context.workOrders.selectedWorkOrderId).toBe(id);
  expect(context.editorSession.openedWorkOrderId).toBe(id);
  expect(context.editVersionDraft.localDraft).toBe(draft);
  expect(context.workOrders.loadError).toMatchObject({
    action: null,
    diagnostics: { code: "INVALID_SERVER_RESPONSE" },
  });
});
it("still closes workspace and clears draft when the selected id is absent in a damaged list", async () => {
  const context = opened();
  http.get.mockResolvedValue({
    data: { workOrders: [{ ...order, id: null }] },
  });
  await context.workOrders.loadAssigned();
  await context.editorSession.reconcileAssignments();
  expect(context.workOrders.items).toHaveLength(1);
  expect(context.workOrders.selectedWorkOrderId).toBeNull();
  expect(context.editorSession.openedWorkOrderId).toBeNull();
  expect(context.editVersionDraft.localDraft).toBeNull();
});
