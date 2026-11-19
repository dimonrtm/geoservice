import {
  createLocalDraft,
  isLocalDraftDirty,
} from "@/domain/workspace/workspaceDraft";
import type { EditorWorkflowPorts } from "../editorWorkflowPorts";

export function createDraftWorkflow(ports: EditorWorkflowPorts) {
  const store = ports.editVersionDraft;

  function beginLocalEdit(featureId: string, vertexIndex: number): boolean {
    const editorNavigation = ports.editorNavigation;
    const editorSession = ports.editorSession;
    const editVersionCommands = ports.editVersionCommands;
    if (
      !ports.editor.readyFor(featureId) ||
      editorNavigation.workspaceInteractionLocked ||
      !editorSession.activeWorkspace ||
      editVersionCommands.storageError ||
      ["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
        editVersionCommands.saveError ?? "",
      ) ||
      editVersionCommands.recoveryRecord ||
      !["idle", "editing", "rejected"].includes(editVersionCommands.phase)
    )
      return false;
    if (store.localDraft) {
      if (
        store.localDraft.featureId === featureId &&
        store.localDraft.vertexIndex === vertexIndex
      )
        return true;
      if (isLocalDraftDirty(store.localDraft)) {
        store.reportEditBlocked("FINISH_OR_CANCEL_LOCAL_WORK");
        return false;
      }
    }
    try {
      store.replaceDraft(
        createLocalDraft(editorSession.activeWorkspace, featureId, vertexIndex),
        ports.context(),
      );
      editVersionCommands.markLocalEditing();
      store.reportEditBlocked(null);
      return true;
    } catch {
      store.reportEditBlocked("INVALID_LOCAL_EDIT");
      return false;
    }
  }
  function moveLocalVertex(xy: [number, number]): boolean {
    const editorNavigation = ports.editorNavigation;
    const editVersionCommands = ports.editVersionCommands;
    if (
      editorNavigation.workspaceInteractionLocked ||
      !store.localDraft ||
      !ports.editor.readyFor(store.localDraft.featureId) ||
      editVersionCommands.storageError ||
      ["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
        editVersionCommands.saveError ?? "",
      ) ||
      editVersionCommands.recoveryRecord ||
      !["editing", "rejected"].includes(editVersionCommands.phase)
    )
      return false;
    try {
      store.moveDraftVertex(xy);
      editVersionCommands.markLocalEditing();
      return true;
    } catch {
      store.reportEditBlocked("INVALID_LOCAL_EDIT");
      return false;
    }
  }
  function cancelLocalEdit(): boolean {
    const editorNavigation = ports.editorNavigation;
    const editVersionCommands = ports.editVersionCommands;
    if (
      editorNavigation.workspaceInteractionLocked ||
      editVersionCommands.storageError ||
      editVersionCommands.readbackError ||
      editVersionCommands.recoveryRecord ||
      !["idle", "editing", "rejected", "stale"].includes(
        editVersionCommands.phase,
      )
    )
      return false;
    if (editVersionCommands.recoveryKey)
      editVersionCommands.removeStaleComparison(
        editVersionCommands.recoveryKey,
      );
    editVersionCommands.hideComparisonPreview();
    store.resetDraftState();
    editVersionCommands.finishLocalEditing();
    store.reportEditBlocked(null);
    return true;
  }
  function discardLocalChangesKeepingSelection(): boolean {
    const editorNavigation = ports.editorNavigation;
    const editVersionCommands = ports.editVersionCommands;
    const editorSession = ports.editorSession;
    const auth = ports.auth;
    if (
      editorNavigation.workspaceInteractionLocked ||
      !auth.isAuthenticated ||
      auth.user?.role !== "editor" ||
      editVersionCommands.hasAccessSuspension(auth.user.id) ||
      !editorSession.activeWorkspace ||
      !store.localDraft ||
      !isLocalDraftDirty(store.localDraft) ||
      editVersionCommands.recoveryRecord ||
      editVersionCommands.storageError ||
      !["editing", "rejected"].includes(editVersionCommands.phase)
    )
      return false;
    const draft = createLocalDraft(
      editorSession.activeWorkspace,
      store.localDraft.featureId,
      store.localDraft.vertexIndex,
    );
    store.replaceDraft(draft, ports.context());
    editVersionCommands.markLocalEditing(true);
    return true;
  }

  return {
    actions: {
      beginLocalEdit,
      moveLocalVertex,
      cancelLocalEdit,
      discardLocalChangesKeepingSelection,
    },
    getters: {},
  };
}
