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
import { fetchEditVersionMap } from "./editVersionMap";
import { fetchEditVersionChangeSet } from "./editVersionChangeSet";
import { fetchFeatureBaseline } from "./featureBaseline";
import { saveFeatureGeometry } from "./editVersions";
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
    await expect(fetchEditVersionMap("other", "ev-1")).rejects.toThrow();
  });
  it("reads the change set without fetching baseline geometry", async () => {
    const value = {
      draftVersionToken: "3",
      hasPersistedChangeSet: false,
      basicValidation: null,
      changeSet: null,
    };
    http.get.mockResolvedValue({ data: value });
    expect(await fetchEditVersionChangeSet("wo-1", "ev-1")).toEqual(value);
    expect(http.get).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/work-orders/wo-1/edit-versions/ev-1/change-set",
      { signal: undefined },
    );
    http.get.mockResolvedValue({
      data: { ...value, hasPersistedChangeSet: true },
    });
    await expect(fetchEditVersionChangeSet("wo-1", "ev-1")).rejects.toThrow();
  });
  it("rejects baseline geometry belonging to another feature", async () => {
    http.get.mockResolvedValue({
      data: { featureId: "other", baselineGeometry: candidate },
    });
    await expect(
      fetchFeatureBaseline("wo-1", "ev-1", "line-1"),
    ).rejects.toThrow();
    expect(http.get).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/work-orders/wo-1/edit-versions/ev-1/features/line-1/baseline",
      { signal: undefined },
    );
  });
});
