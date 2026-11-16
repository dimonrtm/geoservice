import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { editorTestContext } from "@/test/editorTestContext";
import { parseAssignedWorkOrders } from "@/contracts/work_order/work-order-list";
import { useAuthStore } from "../auth";
const http = vi.hoisted(() => ({ post: vi.fn(), get: vi.fn() }));
vi.mock("@/api/http", () => ({ http }));
const id = "aaaaaaaa-1111-4111-8111-111111111111";
const version = "bbbbbbbb-1111-4111-8111-111111111111";
beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
  sessionStorage.clear();
  const auth = useAuthStore();
  auth.token = "token";
  auth.user = { id: "actor", email: "a@example.local", role: "editor" };
});
function setup() {
  const context = editorTestContext();
  context.workOrders.items = parseAssignedWorkOrders({
    workOrders: [
      { id, code: "WO", title: "Наряд", description: null, status: "assigned" },
    ],
  }).workOrders;
  context.workOrders.selectWorkOrder(id);
  return context;
}
it("rejects Open before status update, read reservation or GET", async () => {
  const context = setup();
  http.post.mockResolvedValue({
    data: {
      editVersion: { id: version, workOrderId: version, status: "open" },
    },
  });
  await context.editorSession.openSelectedWorkOrder();
  expect(context.workOrders.items[0]?.status).toBe("assigned");
  expect(context.editorSession.readGenerations).toEqual({});
  expect(http.get).not.toHaveBeenCalled();
  expect(context.editorSession.openedEditVersionId).toBeNull();
  expect(context.editorSession.selectedOpenWorkspaceError).toMatchObject({
    action: null,
    diagnostics: { code: "INVALID_SERVER_RESPONSE" },
  });
  expect(context.editorSession.selectedOpenWorkspaceError?.guidance).toContain(
    "идентификатор наряда",
  );
});
it.each(["selection", "epoch"])(
  "ignores late invalid Open after changed %s",
  async (change) => {
    const context = setup();
    let finish!: (value: unknown) => void;
    http.post.mockReturnValue(
      new Promise((resolve) => {
        finish = resolve;
      }),
    );
    const pending = context.editorSession.openSelectedWorkOrder();
    if (change === "selection") context.workOrders.selectWorkOrder("another");
    else useAuthStore().sessionEpoch++;
    finish({ data: { editVersion: null } });
    await pending;
    expect(context.editorSession.openWorkspaceErrorByWorkOrderId).toEqual({});
    expect(context.editorSession.readGenerations).toEqual({});
    expect(http.get).not.toHaveBeenCalled();
    expect(context.workOrders.items[0]?.status).toBe("assigned");
  },
);
