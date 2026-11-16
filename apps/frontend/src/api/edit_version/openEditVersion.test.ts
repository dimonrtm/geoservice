import { beforeEach, expect, it, vi } from "vitest";
const http = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock("@/api/http", () => ({ http }));
import { openEditVersion } from "./editVersions";
import { WorkOrderResponseError } from "@/contracts/work_order/work-order-response-error";
const workOrderId = "aaaaaaaa-1111-4111-8111-111111111111";
const id = "bbbbbbbb-1111-4111-8111-111111111111";
beforeEach(() => vi.clearAllMocks());
it("returns only the verified Open projection", async () => {
  http.post.mockResolvedValue({
    data: {
      created: true,
      editVersion: {
        id: id.toUpperCase(),
        workOrderId,
        status: "open",
        ownerId: 42,
      },
    },
  });
  expect(await openEditVersion(workOrderId)).toEqual({
    editVersion: { id, workOrderId, status: "open" },
  });
  expect(http.post).toHaveBeenCalledExactlyOnceWith(
    `/api/v1/work-orders/${workOrderId}/edit-versions`,
  );
});
it.each([
  { id, workOrderId: id, status: "open" },
  { id: "", workOrderId, status: "open" },
  { id, workOrderId, status: "closed" },
])("does not return or retry an invalid Open %j", async (editVersion) => {
  http.post.mockResolvedValue({ data: { editVersion } });
  await expect(openEditVersion(workOrderId)).rejects.toBeInstanceOf(
    WorkOrderResponseError,
  );
  expect(http.post).toHaveBeenCalledTimes(1);
});
