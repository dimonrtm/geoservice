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
import {
  presentWorkspaceCommands,
  workspaceCommandState,
} from "./workspaceCommandPresentation";

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
  setActivePinia(createPinia());
  sessionStorage.clear();
});
describe("workspace command presentation", () => {
  it("separates local changes from persisted changes", () => {
    const store = setup(true);
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true),
    ).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: true,
    });
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true),
    ).toMatchObject({
      canSave: true,
      canCancel: true,
      canRevert: true,
    });
    expect(
      presentWorkspaceCommands(workspaceCommandState(), false),
    ).toMatchObject({
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
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true),
    ).toMatchObject({
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
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true),
    ).toMatchObject({
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
      presentWorkspaceCommands(workspaceCommandState(), true).statusText,
    ).toContain("отклонено");
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).statusText,
    ).toContain("не удалось загрузить");
  });
  it("explains storage failure before sending without claiming an unknown result", () => {
    const store = setup();
    vi.spyOn(store.editVersionCommands, "storageError", "get").mockReturnValue(
      "quota",
    );
    const view = presentWorkspaceCommands(workspaceCommandState(), true);
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
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true),
    ).toMatchObject({
      canSave: false,
      canCancel: true,
    });
    store.editVersionDraft.moveLocalVertex([65.1, 44.3]);
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).canSave,
    ).toBe(true);
    store.editVersionDraft.moveLocalVertex([65, 44]);
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).canSave,
    ).toBe(false);
  });
  it("only claims no-op with source evidence and always explains quality", () => {
    const store = setup(true);
    store.editVersionDraft.localDraft = null;
    store.editVersionCommands.localPhase = "idle";
    store.editVersionCommands.commandResult = successFixture();
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).statusText,
    ).toBe("Прежняя операция выполнена");
    store.editVersionCommands.submittedSourceGeometry =
      structuredClone(candidate);
    store.editVersionCommands.submittedCommandId = commandId;
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).statusText,
    ).toBe("Сохранение выполнено без новых изменений");
    store.seed(workspaceFixture());
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true)
        .positionalAccuracyMessage,
    ).toContain("Позиционная точность не проверена");
  });
  it("does not expose an unrecognized technical code", () => {
    const store = setup();
    store.editVersionCommands.localPhase = "blocked";
    store.editVersionCommands.saveError = "PRIVATE_INTERNAL_CODE";
    expect(
      presentWorkspaceCommands(workspaceCommandState(), true).statusText,
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
    const view = presentWorkspaceCommands(workspaceCommandState(), true);
    expect(view.canSave).toBe(false);
    expect(view.statusText).toContain("форма линии недопустима");
  });
});
