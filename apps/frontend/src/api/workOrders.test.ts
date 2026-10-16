import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  candidate,
  commandId,
  successFixture,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
const http = vi.hoisted(() => ({ put: vi.fn(), get: vi.fn(), post: vi.fn() }));
vi.mock("@/api/http", () => ({ http }));
import { fetchWorkspace, saveFeatureGeometry } from "./workOrders";
describe("workOrders client", () => {
  beforeEach(() => vi.clearAllMocks());
  it("sends exact geometry request once and preserves opaque token", async () => {
    const request = {
      commandId,
      draftVersionToken: "  opaque-token  ",
      geometry: candidate,
    };
    http.put.mockResolvedValue({ data: successFixture() });
    await saveFeatureGeometry(target, request);
    expect(http.put).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/work-orders/wo-1/edit-versions/ev-1/features/line-1/geometry",
      request,
    );
  });
  it("does not retry errors", async () => {
    const error = new Error("network");
    http.put.mockRejectedValue(error);
    await expect(
      saveFeatureGeometry(target, {
        commandId,
        draftVersionToken: "a",
        geometry: candidate,
      }),
    ).rejects.toBe(error);
    expect(http.put).toHaveBeenCalledTimes(1);
  });
  it("checks workspace target and shape", async () => {
    http.get.mockResolvedValue({ data: workspaceFixture() });
    await expect(fetchWorkspace("other", "ev-1")).rejects.toThrow();
  });
});
