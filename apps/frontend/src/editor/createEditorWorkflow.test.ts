import { expect, it, vi } from "vitest";
import { createEditorWorkflow } from "./createEditorWorkflow";
import type { EditorWorkflowPorts } from "./editorWorkflowPorts";
import type { RecoveryCompletion } from "@/contracts/workspace/workspace-recovery";
import { successFixture, target } from "@/test/workspaceEditFixture";

vi.mock("pinia", () => {
  throw new Error("Pure workflow must not import Pinia");
});
const context = {
  actorId: "actor",
  sessionEpoch: 1,
  workOrderId: target.workOrderId,
  editVersionId: target.editVersionId,
  workspaceGeneration: 1,
};
const identity = { ...context, draftGeneration: 1 };
const key = JSON.stringify(["actor", target.workOrderId, target.editVersionId]);
function fixture() {
  const completed = vi.fn(),
    finishDraft = vi.fn(),
    navigate = vi.fn();
  const commands = {
    recoveryKey: key,
    activeSaveAttempt: {
      context,
      draftIdentity: identity,
      commandId: "old",
      navigationId: "nav",
    },
    acceptSuccessfulRecovery: completed,
  };
  const draft = { draftIdentity: identity, finishDraft };
  const ports = {
    editVersionCommands: commands,
    editVersionDraft: draft,
    editorNavigation: {
      takeCompletedNavigation: () => ({ kind: "work-order", workOrderId: "B" }),
      performNavigation: navigate,
    },
    auth: { user: { id: "actor" }, sessionEpoch: 1 },
    context: () => context,
  } as unknown as EditorWorkflowPorts;
  const completion: RecoveryCompletion = {
    sessionEpoch: 1,
    record: {
      schemaVersion: 2,
      key,
      revision: 1,
      command: {
        actorId: "actor",
        target,
        request: {
          commandId: "old",
          draftVersionToken: "revision-a",
          geometry: {
            type: "LineString",
            coordinates: [
              [65, 44],
              [65.1, 44.2],
              [65.2, 44],
            ],
          },
        },
      },
      source: null,
      outcome: { kind: "succeeded", result: successFixture("old") },
      readbackRequired: true,
      blocks: [],
      requiresAccessConfirmation: false,
    },
  };
  return {
    workflow: createEditorWorkflow(ports),
    ports,
    commands,
    draft,
    completion,
    completed,
    finishDraft,
    navigate,
  };
}
it("does not accept an earlier command as completion of the current submission", () => {
  const f = fixture();
  f.commands.activeSaveAttempt.commandId = "new";
  f.workflow.completeRecovery(f.completion);
  expect(f.completed).not.toHaveBeenCalled();
  expect(f.finishDraft).not.toHaveBeenCalled();
  expect(f.navigate).not.toHaveBeenCalled();
});
it("does not finish editing a newer local attempt of the same feature", () => {
  const f = fixture();
  f.draft.draftIdentity = { ...identity, draftGeneration: 2 };
  f.workflow.completeRecovery(f.completion);
  expect(f.completed).not.toHaveBeenCalled();
  expect(f.finishDraft).not.toHaveBeenCalled();
  expect(f.navigate).not.toHaveBeenCalled();
});
it("does not apply completion after returning to the same workspace in a later generation", () => {
  const f = fixture();
  f.ports.context = () => ({ ...context, workspaceGeneration: 3 });
  f.workflow.completeRecovery(f.completion);
  expect(f.completed).not.toHaveBeenCalled();
  expect(f.navigate).not.toHaveBeenCalled();
});
it("finishes matching editing before performing its saved navigation", () => {
  const f = fixture();
  f.workflow.completeRecovery(f.completion);
  expect(f.completed).toHaveBeenCalledWith(f.completion);
  expect(f.finishDraft).toHaveBeenCalledWith(identity);
  expect(f.navigate).toHaveBeenCalledWith({
    kind: "work-order",
    workOrderId: "B",
  });
  expect(f.finishDraft.mock.invocationCallOrder[0]).toBeLessThan(
    f.navigate.mock.invocationCallOrder[0]!,
  );
});
