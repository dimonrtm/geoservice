import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  geometry,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
import { readEditVersionSnapshot } from "./useEditVersionEditor";

const reads = vi.hoisted(() => ({
  map: vi.fn(),
  changes: vi.fn(),
  baseline: vi.fn(),
}));
vi.mock("@/api/editVersionMap", () => ({ fetchEditVersionMap: reads.map }));
vi.mock("@/api/editVersionChangeSet", () => ({
  fetchEditVersionChangeSet: reads.changes,
}));
vi.mock("@/api/featureBaseline", () => ({
  fetchFeatureBaseline: reads.baseline,
}));

beforeEach(() => {
  vi.useFakeTimers();
  vi.resetAllMocks();
  const map = workspaceFixture(true);
  reads.map.mockResolvedValue(map);
  reads.changes.mockResolvedValue({
    ...map.workOrder.editVersion,
    changeSet: {
      featureId: target.featureId,
      vertexIndex: 1,
      operation: "updated",
    },
  });
  reads.baseline.mockResolvedValue({
    featureId: target.featureId,
    baselineGeometry: geometry,
  });
});
afterEach(() => vi.useRealTimers());

it.each(["changes", "baseline"] as const)(
  "retries only the failed %s read and retains upstream results for manual retry",
  async (stage) => {
    const checkpoint = {};
    const controller = new AbortController();
    const read = () =>
      readEditVersionSnapshot(
        target.workOrderId,
        target.editVersionId,
        controller.signal,
        checkpoint,
      );
    const dependency = reads[stage];
    for (let attempt = 0; attempt < 5; attempt++)
      dependency.mockRejectedValueOnce(new Error("offline"));
    const pending = expect(read()).rejects.toThrow();
    await vi.advanceTimersByTimeAsync(0);
    for (const [index, delay] of [2000, 5000, 10000, 20000].entries()) {
      expect(dependency).toHaveBeenCalledTimes(index + 1);
      await vi.advanceTimersByTimeAsync(delay - 1);
      expect(dependency).toHaveBeenCalledTimes(index + 1);
      await vi.advanceTimersByTimeAsync(1);
    }
    await pending;
    expect(dependency).toHaveBeenCalledTimes(5);
    expect(reads.map).toHaveBeenCalledTimes(1);
    expect((await read()).workOrder.editVersion.changeSet?.featureId).toBe(
      target.featureId,
    );
    expect(dependency).toHaveBeenCalledTimes(6);
    expect(reads.map).toHaveBeenCalledTimes(1);
    if (stage === "baseline") expect(reads.changes).toHaveBeenCalledTimes(1);
  },
);

it("discards a late baseline response after cancellation", async () => {
  const controller = new AbortController();
  let resolve!: (value: unknown) => void;
  reads.baseline.mockImplementation(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  const pending = readEditVersionSnapshot(
    target.workOrderId,
    target.editVersionId,
    controller.signal,
  );
  await vi.advanceTimersByTimeAsync(0);
  controller.abort();
  resolve({ featureId: target.featureId, baselineGeometry: geometry });
  await expect(pending).rejects.toThrow();
});
