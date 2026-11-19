import { createLocalDraft } from "@/domain/workspace/workspaceDraft";
import { installEditorRuntime } from "@/editor/editorRuntime";
import { useEditVersionCommandsStore } from "@/stores/edit_version/editVersionCommands";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { useEditorNavigationStore } from "@/stores/editor_navigation/editorNavigation";
import { target, workspaceFixture } from "@/test/workspaceEditFixture";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, expect, it } from "vitest";

const identity = {
  actorId: "actor",
  sessionEpoch: 1,
  workOrderId: target.workOrderId,
  editVersionId: target.editVersionId,
  workspaceGeneration: 1,
  draftGeneration: 1,
};
beforeEach(() => installEditorRuntime(setActivePinia(createPinia())!));

it("a completion for an earlier visit cannot clear a new draft of the same feature", () => {
  const store = useEditVersionDraftStore();
  const draft = createLocalDraft(workspaceFixture(), target.featureId, 1);
  store.startDraft(identity, draft);
  store.startDraft(
    { ...identity, workspaceGeneration: 3, draftGeneration: 2 },
    draft,
  );
  expect(store.finishDraft(identity)).toBe(false);
  expect(store.localDraft).toEqual(draft);
  expect(
    store.finishDraft({
      ...identity,
      workspaceGeneration: 3,
      draftGeneration: 2,
    }),
  ).toBe(true);
  expect(store.localDraft).toBeNull();
});

it("navigation is consumed once and only by its original command and epoch", () => {
  const store = useEditorNavigationStore();
  const key = JSON.stringify([
    identity.actorId,
    identity.workOrderId,
    identity.editVersionId,
  ]);
  const attempt = {
    context: identity,
    draftIdentity: identity,
    commandId: "command",
    navigationId: "nav",
  };
  store.beginNavigation({
    id: "nav",
    actorId: "actor",
    sessionEpoch: 1,
    sourceKey: key,
    target: { kind: "work-order", workOrderId: "B" },
    phase: "dirty",
    commandId: null,
  });
  expect(store.bindNavigationSave("nav", attempt)).toBe(true);
  expect(
    store.takeCompletedNavigation({ ...attempt, commandId: "old" }),
  ).toBeNull();
  expect(
    store.takeCompletedNavigation({
      ...attempt,
      context: { ...identity, sessionEpoch: 2 },
    }),
  ).toBeNull();
  expect(store.takeCompletedNavigation(attempt)).toEqual({
    kind: "work-order",
    workOrderId: "B",
  });
  expect(store.takeCompletedNavigation(attempt)).toBeNull();
});

it("aborting an old navigation preserves the newer confirmation", () => {
  const store = useEditorNavigationStore();
  store.beginNavigation({
    id: "new",
    actorId: "actor",
    sessionEpoch: 1,
    sourceKey: null,
    target: { kind: "logout" },
    phase: "dirty",
    commandId: null,
  });
  store.abortNavigation("old");
  expect(store.navigation?.id).toBe("new");
});

it("cancel then a new attempt in the same workspace cannot reuse draft identity", () => {
  const store = useEditVersionDraftStore();
  const draft = createLocalDraft(workspaceFixture(), target.featureId, 1);
  store.replaceDraft(draft, identity);
  const old = { ...store.draftIdentity! };
  store.resetDraftState();
  store.replaceDraft(draft, identity);
  expect(store.finishDraft(old)).toBe(false);
  expect(store.localDraft).not.toBeNull();
});

it("hiding a comparison preserves material and unavailable source cannot be previewed", () => {
  const store = useEditVersionCommandsStore();
  store.staleComparisons.a = {
    source: null,
    candidate: {
      type: "LineString",
      coordinates: [
        [0, 0],
        [1, 1],
        [2, 0],
      ],
    },
    commandId: "a",
    featureId: "f",
  };
  store.comparisonPreview = "candidate";
  store.hideComparisonPreview();
  expect(store.staleComparisons.a).toBeDefined();
  expect(store.comparisonPreview).toBeNull();
  expect(store.showComparisonPreview("source")).toBe(false);
  store.resetForeground(true);
  expect(store.staleComparisons.a).toBeDefined();
});
