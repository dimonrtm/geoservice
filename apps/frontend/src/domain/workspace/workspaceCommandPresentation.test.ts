import { describe, expect, it, vi } from "vitest";
import {
  candidate,
  geometry,
  successFixture,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
import {
  presentWorkspaceCommands,
  type WorkspaceCommandState,
} from "./workspaceCommandPresentation";
vi.mock("@/composables/edit_version/useEditVersionEditor", () => {
  throw new Error("Presenter imported editor");
});
function state(): WorkspaceCommandState {
  const workspace = workspaceFixture();
  workspace.workOrder.scope.aoi.geometry = {
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
  return {
    activeWorkspace: workspace,
    localDraft: {
      featureId: "line-1",
      vertexIndex: 1,
      sourceGeometry: geometry,
      candidateGeometry: candidate,
      sourceToken: "a",
    },
    phase: "editing",
    recoveryRecord: null,
    commandResult: null,
    saveError: null,
    readbackError: null,
    storageError: null,
    didSaveChangeGeometry: null,
    rejectedCandidateGeometry: null,
    canRetryPendingCommand: false,
    canRetryCurrentRead: false,
    canDiscardRejectedAttempt: false,
    workspaceInteractionLocked: false,
    revertBaselineReady: true,
    draftBaselineReady: true,
  };
}
describe("pure workspace command presentation", () => {
  it("computes actions without Pinia", () => {
    expect(presentWorkspaceCommands(state(), true)).toMatchObject({
      canSave: true,
      canCancel: true,
      canRevert: false,
    });
    expect(presentWorkspaceCommands(state(), false).canSave).toBe(false);
  });
  it.each([
    "sending",
    "retry-wait",
    "unknown",
    "reading-current",
    "stale",
    "blocked",
  ] as const)("blocks editing during %s", (phase) => {
    expect(presentWorkspaceCommands({ ...state(), phase }, true)).toMatchObject(
      { canSave: false, canCancel: false, canRevert: false },
    );
  });
  it("keeps success distinct from rejection when readback fails", () => {
    const input = state();
    input.readbackError = "GET failed";
    const command = {
      actorId: "actor",
      target: {
        workOrderId: "wo-1",
        editVersionId: "ev-1",
        featureId: "line-1",
      },
      request: { commandId: "id", draftVersionToken: "a", geometry: candidate },
    };
    input.recoveryRecord = {
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    };
    expect(presentWorkspaceCommands(input, true)).toMatchObject({
      canSave: false,
      statusText:
        "Операция выполнена, но актуальные данные карты не удалось загрузить. Редактирование временно недоступно",
    });
    input.recoveryRecord = {
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
    expect(presentWorkspaceCommands(input, true).statusText).toContain(
      "отклонено",
    );
  });
  it("keeps dialog and storage blocks ahead of editing", () => {
    expect(
      presentWorkspaceCommands(
        { ...state(), workspaceInteractionLocked: true },
        true,
      ).canSave,
    ).toBe(false);
    expect(
      presentWorkspaceCommands({ ...state(), storageError: "quota" }, true)
        .statusText,
    ).toContain("не отправлена");
  });
  it("requires baseline and a corrected rejected candidate", () => {
    expect(
      presentWorkspaceCommands({ ...state(), draftBaselineReady: false }, true)
        .canSave,
    ).toBe(false);
    expect(
      presentWorkspaceCommands(
        {
          ...state(),
          rejectedCandidateGeometry: candidate,
          saveError: "GEOMETRY_INVALID",
        },
        true,
      ),
    ).toMatchObject({ canSave: false, canCancel: true });
  });
  it.each([
    [null, "Прежняя операция выполнена"],
    [false, "Сохранение выполнено без новых изменений"],
    [true, "Правка сохранена в рабочей версии"],
  ] as const)("uses source evidence for success %s", (changed, message) => {
    expect(
      presentWorkspaceCommands(
        {
          ...state(),
          localDraft: null,
          commandResult: successFixture(),
          didSaveChangeGeometry: changed,
        },
        true,
      ).statusText,
    ).toBe(message);
  });
});
