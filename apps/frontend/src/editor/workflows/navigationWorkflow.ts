import { isLocalDraftDirty } from "@/domain/workspace/workspaceDraft";
import type {
  NavigationChoice,
  NavigationTarget,
} from "@/domain/workspace/workspaceNavigation";
import type { EditorWorkflowPorts } from "../editorWorkflowPorts";

export function createNavigationWorkflow(ports: EditorWorkflowPorts) {
  const store = ports.editorNavigation;

  function get_workspaceInteractionLocked(): boolean {
    const editVersionCommands = ports.editVersionCommands;
    return (
      (store.logoutAttempt !== null &&
        store.logoutAttempt.sessionId === ports.auth.sessionId &&
        store.logoutAttempt.sessionEpoch === ports.auth.sessionEpoch) ||
      editVersionCommands.revertConfirmation !== null ||
      (store.navigation !== null && store.navigation.phase !== "saving")
    );
  }
  function get_canLeaveWorkspace(): boolean {
    const editVersionCommands = ports.editVersionCommands;
    const editVersionDraft = ports.editVersionDraft;
    return (
      !store.workspaceInteractionLocked &&
      !editVersionCommands.revertConfirmation &&
      (!editVersionDraft.localDraft ||
        !isLocalDraftDirty(editVersionDraft.localDraft) ||
        !!editVersionCommands.recoveryRecord ||
        editVersionCommands.phase === "stale")
    );
  }
  function requestNavigation(target: NavigationTarget): string | null {
    const editVersionCommands = ports.editVersionCommands;
    const workOrders = ports.workOrders;
    const editVersionDraft = ports.editVersionDraft;
    const auth = ports.auth;
    if (
      !auth.user ||
      store.workspaceInteractionLocked ||
      editVersionCommands.revertConfirmation ||
      store.navigation ||
      (target.kind === "work-order" &&
        target.workOrderId === workOrders.selectedWorkOrderId)
    )
      return null;
    const recovery = ports.recovery;
    const sent =
      target.kind === "logout"
        ? Object.values(recovery.records).some(
            (r) => r.command.actorId === auth.user!.id,
          )
        : !!editVersionCommands.recoveryRecord;
    const stale =
      target.kind === "logout"
        ? Object.keys(editVersionCommands.staleComparisons).length > 0
        : !!(
            editVersionCommands.recoveryKey &&
            editVersionCommands.staleComparisons[
              editVersionCommands.recoveryKey
            ]
          );
    const dirty =
      !!editVersionDraft.localDraft &&
      isLocalDraftDirty(editVersionDraft.localDraft) &&
      !editVersionCommands.recoveryRecord &&
      !editVersionCommands.activeComparison;
    if (!dirty && !sent && !stale) {
      void store.performNavigation(target);
      return null;
    }
    const id = ports.createCommandId();
    store.beginNavigation({
      id,
      actorId: auth.user.id,
      sessionEpoch: auth.sessionEpoch,
      sourceKey: editVersionCommands.recoveryKey,
      target,
      phase: dirty ? "dirty" : sent ? "sent" : "stale",
      commandId: null,
    });
    return id;
  }
  function cancelNavigation(id: string): void {
    store.abortNavigation(id);
  }
  async function prepareLogout(): Promise<boolean> {
    const auth = ports.auth;
    const actor = auth.user?.id;
    if (!actor) return true;
    const sid = auth.sessionId;
    const epoch = auth.sessionEpoch;
    const recovery = ports.recovery;
    const ready = await recovery.prepareActorLogout(actor);
    if (auth.sessionId !== sid || auth.sessionEpoch !== epoch) return false;
    if (!ready) {
      store.reportLogoutPreparation(false);
      return false;
    }
    store.reportLogoutPreparation(true);
    return true;
  }
  async function performNavigation(target: NavigationTarget): Promise<void> {
    const editorSession = ports.editorSession;
    const workOrders = ports.workOrders;
    if (target.kind === "logout") {
      const auth = ports.auth;
      if (store.logoutAttempt || !auth.sessionId) return;
      const attempt = {
        id: ports.createCommandId(),
        sessionId: auth.sessionId,
        sessionEpoch: auth.sessionEpoch,
      };
      store.startLogoutAttempt(attempt);
      const isCurrent = () =>
        auth.sessionId === attempt.sessionId &&
        auth.sessionEpoch === attempt.sessionEpoch;
      try {
        if (!(await store.prepareLogout()) || !isCurrent()) return;
        const ended = await auth.logout();
        if (ended && isCurrent()) auth.clearLocalSession();
      } finally {
        store.finishLogoutAttempt(attempt.id);
      }
      return;
    }
    if (store.workspaceInteractionLocked) return;
    editorSession.clearOpenedWorkspace({ force: true });
    workOrders.selectWorkOrder(target.workOrderId);
  }
  async function resolveNavigation(
    id: string,
    choice: NavigationChoice,
  ): Promise<void> {
    const editVersionCommands = ports.editVersionCommands;
    const editVersionDraft = ports.editVersionDraft;
    const context = store.navigation,
      auth = ports.auth;
    if (!context || context.id !== id || context.phase === "saving") return;
    if (
      context.actorId !== auth.user?.id ||
      context.sessionEpoch !== auth.sessionEpoch ||
      context.sourceKey !== editVersionCommands.recoveryKey
    ) {
      store.abortNavigation(id);
      return;
    }
    if (choice === "stay") {
      store.abortNavigation(id);
      return;
    }
    if (choice === "save" && context.phase === "dirty") {
      store.startNavigationSave(id);
      await editVersionCommands.saveLocalDraft();
      if (store.navigation?.id === id && !store.navigation.commandId)
        store.abortNavigation(id);
      return;
    }
    if (
      (choice === "discard" && context.phase === "dirty") ||
      (choice === "leave" && context.phase !== "dirty")
    ) {
      store.abortNavigation(id);
      if (choice === "discard") editVersionDraft.cancelLocalEdit();
      await store.performNavigation(context.target);
    }
  }
  function allowWorkspaceNavigation(): boolean {
    const editVersionDraft = ports.editVersionDraft;
    if (store.canLeaveWorkspace) return true;
    editVersionDraft.reportEditBlocked("FINISH_OR_CANCEL_LOCAL_WORK");
    return false;
  }

  return {
    actions: {
      requestNavigation,
      cancelNavigation,
      prepareLogout,
      performNavigation,
      resolveNavigation,
      allowWorkspaceNavigation,
    },
    getters: {
      workspaceInteractionLocked: get_workspaceInteractionLocked,
      canLeaveWorkspace: get_canLeaveWorkspace,
    },
  };
}
