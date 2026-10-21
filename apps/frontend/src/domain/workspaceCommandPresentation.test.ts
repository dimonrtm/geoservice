import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useWorkOrdersStore } from "@/stores/workOrders";
import {
  workspaceFixture,
  target,
  successFixture,
  commandId,
  candidate,
} from "@/test/workspaceEditFixture";
import { presentWorkspaceCommands } from "./workspaceCommandPresentation";

function setup(changed = false) {
  const store = useWorkOrdersStore();
  store.workspace = workspaceFixture(changed);
  store.workspace.workOrder.scope.aoi.geometry = {
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
  store.openedWorkOrderId = store.selectedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  store.beginLocalEdit(target.featureId, 1);
  return store;
}
beforeEach(() => {
  setActivePinia(createPinia());
  sessionStorage.clear();
});
describe("workspace command presentation", () => {
  it("separates local changes from persisted changes", () => {
    const store = setup(true);
    expect(presentWorkspaceCommands(store, true)).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: true,
    });
    store.moveLocalVertex([65.1, 44.3]);
    expect(presentWorkspaceCommands(store, true)).toMatchObject({
      canSave: true,
      canCancel: true,
      canRevert: true,
    });
    expect(presentWorkspaceCommands(store, false)).toMatchObject({
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
    store.moveLocalVertex([65.1, 44.3]);
    store.phase = phase;
    expect(presentWorkspaceCommands(store, true)).toMatchObject({
      canSave: false,
      canCancel: false,
      canRevert: false,
    });
  });
  it("distinguishes known success and stale when current cannot be read", () => {
    const store = setup();
    store.phase = "reading-current";
    store.readbackError = "GET failed";
    const command = {
      actorId: "actor",
      target,
      request: { commandId, draftVersionToken: "a", geometry: candidate },
    };
    store.recoveryRecord = {
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    };
    expect(presentWorkspaceCommands(store, true)).toMatchObject({
      busy: false,
      statusText:
        "Операция выполнена, но актуальные данные карты не удалось загрузить. Редактирование временно недоступно",
    });
    store.recoveryRecord = {
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
    };
    expect(presentWorkspaceCommands(store, true).statusText).toContain(
      "отклонено",
    );
    expect(presentWorkspaceCommands(store, true).statusText).toContain(
      "не удалось загрузить",
    );
  });
  it("explains storage failure before sending without claiming an unknown result", () => {
    const store = setup();
    store.storageError = "quota";
    const view = presentWorkspaceCommands(store, true);
    expect(view.canSave).toBe(false);
    expect(view.busy).toBe(false);
    expect(view.statusText).toContain("не отправлена");
  });
  it("blocks invalid and unchanged rejected geometry but allows correction", () => {
    const store = setup();
    store.moveLocalVertex([65.1, 44.2]);
    store.rejectedCandidateGeometry = structuredClone(candidate);
    store.phase = "rejected";
    store.saveError = "GEOMETRY_INVALID";
    expect(presentWorkspaceCommands(store, true)).toMatchObject({
      canSave: false,
      canCancel: true,
    });
    store.moveLocalVertex([65.1, 44.3]);
    expect(presentWorkspaceCommands(store, true).canSave).toBe(true);
    store.moveLocalVertex([65, 44]);
    expect(presentWorkspaceCommands(store, true).canSave).toBe(false);
  });
  it("only claims no-op with source evidence and always explains quality", () => {
    const store = setup(true);
    store.localDraft = null;
    store.phase = "idle";
    store.commandResult = successFixture();
    expect(presentWorkspaceCommands(store, true).statusText).toBe(
      "Правка сохранена в рабочей версии",
    );
    store.submittedSourceGeometry = structuredClone(candidate);
    store.submittedCommandId = commandId;
    expect(presentWorkspaceCommands(store, true).statusText).toBe(
      "Сохранение выполнено без новых изменений",
    );
    store.workspace = workspaceFixture();
    expect(
      presentWorkspaceCommands(store, true).positionalAccuracyMessage,
    ).toContain("Позиционная точность не проверена");
  });
  it("does not expose an unrecognized technical code", () => {
    const store = setup();
    store.phase = "blocked";
    store.saveError = "PRIVATE_INTERNAL_CODE";
    expect(presentWorkspaceCommands(store, true).statusText).not.toContain(
      "PRIVATE_INTERNAL_CODE",
    );
  });
  it("explains the disabled Save when returning to a rejected candidate", () => {
    const store = setup();
    store.moveLocalVertex([65.1, 44.2]);
    store.rejectedCandidateGeometry = structuredClone(candidate);
    store.saveError = "GEOMETRY_INVALID";
    store.phase = "rejected";
    store.moveLocalVertex([65.1, 44.3]);
    store.moveLocalVertex([65.1, 44.2]);
    const view = presentWorkspaceCommands(store, true);
    expect(view.canSave).toBe(false);
    expect(view.statusText).toContain("форма линии недопустима");
  });
});
