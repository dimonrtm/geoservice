import { installEditorRuntime } from "@/editor/editorRuntime";
import { useFeatureBaselineStore } from "@/stores/edit_version/featureBaseline";
import { geometry } from "@/test/workspaceEditFixture";
import { editorTestContext } from "@/test/editorTestContext";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  workspaceFixture,
  target,
  successFixture,
  commandId,
  candidate,
} from "@/test/workspaceEditFixture";
import { useWorkspaceCommandPresentation } from "./useWorkspaceCommandPresentation";
import { ref } from "vue";

function setup(changed = false) {
  const store = editorTestContext();
  store.seed(workspaceFixture(changed));
  store.editor.snapshot!.workOrder.scope.aoi.geometry = {
    type: "Polygon",
    coordinates: [
      [
        [64, 43],
        [66, 43],
        [66, 45],
        [64, 45],
        [64, 43],
      ],
    ],
  };
  store.editorSession.openedWorkOrderId = store.workOrders.selectedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  store.editVersionDraft.beginLocalEdit(target.featureId, 1);
  return store;
}
beforeEach(() => {
  installEditorRuntime(setActivePinia(createPinia())!);
  sessionStorage.clear();
});
describe("workspace command presentation", () => {
  it("separates local changes from persisted changes", () => {
    const store = setup(true);
    expect(useWorkspaceCommandPresentation(() => true).value).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: true,
    });
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    expect(useWorkspaceCommandPresentation(() => true).value).toMatchObject({
      canSave: true,
      canCancel: true,
      canRevert: true,
    });
    expect(useWorkspaceCommandPresentation(() => false).value).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: false,
    });
  });
  it.each([
    "sending",
    "retry-wait",
    "unknown",
    "reading-current",
    "stale",
    "blocked",
  ] as const)("blocks every command during %s", (phase) => {
    const store = setup(true);
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    store.editVersionCommands.localPhase = phase;
    expect(useWorkspaceCommandPresentation(() => true).value).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: false,
    });
  });
  it("distinguishes known success and stale when current cannot be read", () => {
    const store = setup();
    store.editVersionCommands.localPhase = "reading-current";
    vi.spyOn(store.editVersionCommands, "readbackError", "get").mockReturnValue(
      "GET failed",
    );
    const command = {
      actorId: "actor",
      target,
      request: { commandId, draftVersionToken: "a", geometry: candidate },
    };
    vi.spyOn(
      store.editVersionCommands,
      "recoveryRecord",
      "get",
    ).mockReturnValue({
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    });
    expect(useWorkspaceCommandPresentation(() => true).value).toMatchObject({
      busy: false,
      statusText:
        "Операция выполнена, но актуальные данные карты не удалось загрузить. Редактирование временно недоступно",
    });
    vi.spyOn(
      store.editVersionCommands,
      "recoveryRecord",
      "get",
    ).mockReturnValue({
      schemaVersion: 1,
      command,
      state: "rejected",
      needsReadback: true,
      error: {
        status: 409,
        code: "DRAFT_VERSION_STALE",
        message: "stale",
        correlationId: null,
      },
    });
    expect(
      useWorkspaceCommandPresentation(() => true).value.statusText,
    ).toContain("отклонено");
    expect(
      useWorkspaceCommandPresentation(() => true).value.statusText,
    ).toContain("не удалось загрузить");
  });
  it("explains storage failure before sending without claiming an unknown result", () => {
    const store = setup();
    vi.spyOn(store.editVersionCommands, "storageError", "get").mockReturnValue(
      "quota",
    );
    const view = useWorkspaceCommandPresentation(() => true).value;
    expect(view.canSave).toBe(false);
    expect(view.busy).toBe(false);
    expect(view.statusText).toContain("не отправлена");
  });
  it("blocks invalid and unchanged rejected geometry but allows correction", () => {
    const store = setup();
    store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
    store.editVersionCommands.rejectedCandidateGeometry =
      structuredClone(candidate);
    store.editVersionCommands.localPhase = "rejected";
    store.editVersionCommands.saveError = "GEOMETRY_INVALID";
    expect(useWorkspaceCommandPresentation(() => true).value).toMatchObject({
      canSave: false,
      canCancel: true,
    });
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    expect(useWorkspaceCommandPresentation(() => true).value.canSave).toBe(
      true,
    );
    store.editVersionDraft.moveLocalVertex([65, 44]);
    expect(useWorkspaceCommandPresentation(() => true).value.canSave).toBe(
      false,
    );
  });
  it("only claims no-op with source evidence and always explains quality", () => {
    const store = setup(true);
    store.editVersionDraft.localDraft = null;
    store.editVersionCommands.localPhase = "idle";
    store.editVersionCommands.commandResult = successFixture();
    expect(useWorkspaceCommandPresentation(() => true).value.statusText).toBe(
      "Прежняя операция выполнена",
    );
    store.editVersionCommands.submittedSourceGeometry =
      structuredClone(candidate);
    store.editVersionCommands.submittedCommandId = commandId;
    expect(useWorkspaceCommandPresentation(() => true).value.statusText).toBe(
      "Сохранение выполнено без новых изменений",
    );
    store.seed(workspaceFixture());
    expect(
      useWorkspaceCommandPresentation(() => true).value
        .positionalAccuracyMessage,
    ).toContain("Позиционная точность не проверена");
  });
  it("does not expose an unrecognized technical code", () => {
    const store = setup();
    store.editVersionCommands.localPhase = "blocked";
    store.editVersionCommands.saveError = "PRIVATE_INTERNAL_CODE";
    expect(
      useWorkspaceCommandPresentation(() => true).value.statusText,
    ).not.toContain("PRIVATE_INTERNAL_CODE");
  });
  it("explains the disabled Save when returning to a rejected candidate", () => {
    const store = setup();
    store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
    store.editVersionCommands.rejectedCandidateGeometry =
      structuredClone(candidate);
    store.editVersionCommands.saveError = "GEOMETRY_INVALID";
    store.editVersionCommands.localPhase = "rejected";
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
    const view = useWorkspaceCommandPresentation(() => true).value;
    expect(view.canSave).toBe(false);
    expect(view.statusText).toContain("форма линии недопустима");
  });
});

it("updates the same computed view when permission and draft change", () => {
  const store = setup();
  const allowed = ref(true);
  const view = useWorkspaceCommandPresentation(() => allowed.value);
  expect(view.value.canSave).toBe(false);
  store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
  expect(view.value.canSave).toBe(true);
  allowed.value = false;
  expect(view.value.canSave).toBe(false);
  allowed.value = true;
  store.editVersionCommands.localPhase = "sending";
  expect(view.value.busy).toBe(true);
});

it("reacts to baseline readiness and navigation lock on the same computed", () => {
  const store = setup(true);
  store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
  const baseline = useFeatureBaselineStore();
  const view = useWorkspaceCommandPresentation(() => true);
  expect(view.value).toMatchObject({ canSave: true, canRevert: true });
  baseline.reset();
  expect(view.value).toMatchObject({ canSave: false, canRevert: false });
  baseline.accept({ featureId: target.featureId, baselineGeometry: geometry });
  expect(view.value).toMatchObject({ canSave: true, canRevert: true });
  store.editVersionDraft.localDraft!.featureId = "different-feature";
  expect(view.value).toMatchObject({ canSave: false, canRevert: true });
  store.editorNavigation.navigation = {
    id: "navigation",
    actorId: "actor",
    sessionEpoch: 0,
    sourceKey: null,
    target: { kind: "work-order", workOrderId: "other" },
    phase: "dirty",
    commandId: null,
  };
  expect(view.value).toMatchObject({ canSave: false, canRevert: false });
  store.editorNavigation.navigation = null;
  expect(view.value.canRevert).toBe(true);
});
