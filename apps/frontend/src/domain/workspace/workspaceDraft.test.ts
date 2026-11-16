import { describe, expect, it } from "vitest";
import {
  createLocalDraft,
  updateLocalVertex,
  isLocalDraftDirty,
} from "./workspaceDraft";
import { workspaceFixture, target } from "@/test/workspaceEditFixture";
describe("local line draft", () => {
  it("does not mutate current and measures dirty relative to current", () => {
    const ws = workspaceFixture(true);
    const draft = createLocalDraft(ws, target.featureId, 1);
    expect(isLocalDraftDirty(draft)).toBe(false);
    const moved = updateLocalVertex(draft, [65.1, 44.3]);
    expect(isLocalDraftDirty(moved)).toBe(true);
    expect(draft.candidateGeometry.coordinates[1]).toEqual([65.1, 44.2]);
    expect(ws.workOrder.editVersion.features.features[0]?.geometry).toEqual(
      draft.sourceGeometry,
    );
  });
  it("rejects endpoints, nonline and wrong persisted vertex", () => {
    expect(() =>
      createLocalDraft(workspaceFixture(), target.featureId, 0),
    ).toThrow();
    expect(() =>
      createLocalDraft(workspaceFixture(true), "other", 1),
    ).toThrow();
    expect(() =>
      updateLocalVertex(
        createLocalDraft(workspaceFixture(), target.featureId, 1),
        [NaN, 2],
      ),
    ).toThrow();
  });
});
