import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { workspaceFixture, geometry } from "@/test/workspaceEditFixture";
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
import { useEditVersionEditor } from "./useEditVersionEditor";
beforeEach(() => {
  setActivePinia(createPinia());
  vi.useFakeTimers();
  vi.resetAllMocks();
  reads.map.mockResolvedValue(workspaceFixture());
  reads.changes.mockResolvedValue({
    draftVersionToken: "revision-a",
    hasPersistedChangeSet: false,
    basicValidation: null,
    changeSet: null,
  });
  reads.baseline.mockResolvedValue({
    featureId: "line-1",
    baselineGeometry: geometry,
  });
});
afterEach(() => vi.useRealTimers());
it("loads the selected line when the initial change set finishes", async () => {
  const editor = useEditVersionEditor();
  let finish!: (value: unknown) => void;
  reads.changes.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const opening = editor.open("wo-1", "ev-1");
  await vi.advanceTimersByTimeAsync(0);
  await editor.selectFeature("line-1");
  expect(reads.baseline).not.toHaveBeenCalled();
  finish({
    draftVersionToken: "revision-a",
    hasPersistedChangeSet: false,
    basicValidation: null,
    changeSet: null,
  });
  await opening;
  expect(editor.readyFor("line-1")).toBe(true);
});
it("keeps the last map and offers a retry if refreshing a mismatched token fails", async () => {
  const editor = useEditVersionEditor();
  const saved = workspaceFixture(true);
  reads.changes.mockResolvedValue({
    ...saved.workOrder.editVersion,
    changeSet: { featureId: "line-1", vertexIndex: 1, operation: "updated" },
  });
  reads.map
    .mockResolvedValueOnce(workspaceFixture())
    .mockRejectedValueOnce(new Error("map offline"))
    .mockResolvedValue(saved);
  expect(await editor.open("wo-1", "ev-1")).toBeNull();
  expect(editor.snapshot?.workOrder.editVersion.draftVersionToken).toBe(
    "revision-a",
  );
  expect(editor.canRetry).toBe(true);
  expect(editor.readyFor("line-1")).toBe(false);
  await editor.retry();
  expect(editor.readyFor("line-1")).toBe(true);
});
it("keeps the map after five failed change reads and retries that read alone", async () => {
  const editor = useEditVersionEditor();
  reads.changes.mockRejectedValue(new Error("offline"));
  const opening = editor.open("wo-1", "ev-1");
  await vi.advanceTimersByTimeAsync(0);
  expect(editor.snapshot?.workOrder.id).toBe("wo-1");
  expect(editor.readyFor("line-1")).toBe(false);
  for (const delay of [2000, 5000, 10000, 20000])
    await vi.advanceTimersByTimeAsync(delay);
  await opening;
  expect(reads.changes).toHaveBeenCalledTimes(5);
  expect(editor.canRetry).toBe(true);
  reads.changes.mockResolvedValue({
    draftVersionToken: "revision-a",
    hasPersistedChangeSet: false,
    basicValidation: null,
    changeSet: null,
  });
  await editor.retry();
  expect(reads.map).toHaveBeenCalledTimes(1);
  await editor.selectFeature("line-1");
  expect(editor.readyFor("line-1")).toBe(true);
});
it("re-reads both tokens and automatically loads the saved feature baseline", async () => {
  const editor = useEditVersionEditor();
  const saved = workspaceFixture(true);
  const { changeSet, ...version } = saved.workOrder.editVersion;
  reads.map.mockResolvedValueOnce(workspaceFixture()).mockResolvedValue(saved);
  reads.changes.mockResolvedValue({
    ...version,
    changeSet: { featureId: "line-1", vertexIndex: 1, operation: "updated" },
  });
  await editor.open("wo-1", "ev-1");
  expect(reads.map).toHaveBeenCalledTimes(2);
  expect(reads.changes).toHaveBeenCalledTimes(2);
  expect(reads.baseline).toHaveBeenCalledTimes(1);
  expect(editor.snapshot?.workOrder.editVersion.changeSet).toEqual(changeSet);
  expect(editor.readyFor("line-1")).toBe(true);
});

it("retries only the selected baseline after exhausting its own attempts", async () => {
  const editor = useEditVersionEditor();
  await editor.open("wo-1", "ev-1");
  reads.baseline.mockRejectedValue(new Error("offline"));
  const selecting = editor.selectFeature("line-1");
  await vi.advanceTimersByTimeAsync(37000);
  await selecting;
  expect(reads.baseline).toHaveBeenCalledTimes(5);
  expect(editor.readyFor("line-1")).toBe(false);
  reads.baseline.mockResolvedValue({
    featureId: "line-1",
    baselineGeometry: geometry,
  });
  await editor.retry();
  expect(reads.changes).toHaveBeenCalledTimes(1);
  expect(reads.map).toHaveBeenCalledTimes(1);
  expect(editor.readyFor("line-1")).toBe(true);
});

it("discards a late response after the session closes", async () => {
  const editor = useEditVersionEditor();
  let finish!: (value: unknown) => void;
  reads.changes.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const opening = editor.open("wo-1", "ev-1");
  await vi.advanceTimersByTimeAsync(0);
  editor.reset();
  finish({
    draftVersionToken: "revision-a",
    hasPersistedChangeSet: false,
    basicValidation: null,
    changeSet: null,
  });
  expect(await opening).toBeNull();
  expect(editor.snapshot).toBeNull();
  expect(editor.readyFor("line-1")).toBe(false);
});
