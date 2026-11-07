import { defineStore } from "pinia";
import { isLocalDraftDirty } from "@/domain/workspaceDraft";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import type {
  NavigationTarget,
  NavigationChoice,
  NavigationContext,
} from "@/domain/workspaceNavigation";

import { useEditVersionDraftStore } from "@/stores/editVersionDraft";
import { useEditVersionCommandsStore } from "@/stores/editVersionCommands";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useEditorSessionStore } from "@/stores/editorSession";
type EditorNavigationState = {
  navigation: NavigationContext | null;
  navigationError: string | null;
  logoutAttempt: { id: string; sessionId: string; sessionEpoch: number } | null;
};

export const useEditorNavigationStore = defineStore("editorNavigation", {
  state: (): EditorNavigationState => ({
    navigation: null,
    navigationError: null,
    logoutAttempt: null,
  }),
  getters: {
    workspaceInteractionLocked: (state): boolean => {
      const editVersionCommands = useEditVersionCommandsStore();
      return (
        (state.logoutAttempt !== null &&
          state.logoutAttempt.sessionId === useAuthStore().sessionId &&
          state.logoutAttempt.sessionEpoch === useAuthStore().sessionEpoch) ||
        editVersionCommands.revertConfirmation !== null ||
        (state.navigation !== null && state.navigation.phase !== "saving")
      );
    },
    canLeaveWorkspace(): boolean {
      const editVersionCommands = useEditVersionCommandsStore();
      const editVersionDraft = useEditVersionDraftStore();
      return (
        !this.workspaceInteractionLocked &&
        !editVersionCommands.revertConfirmation &&
        (!editVersionDraft.localDraft ||
          !isLocalDraftDirty(editVersionDraft.localDraft) ||
          !!editVersionCommands.recoveryRecord ||
          editVersionCommands.phase === "stale")
      );
    },
  },
  actions: {
    requestNavigation(target: NavigationTarget): string | null {
      const editVersionCommands = useEditVersionCommandsStore();
      const workOrders = useWorkOrdersStore();
      const editVersionDraft = useEditVersionDraftStore();
      const auth = useAuthStore();
      if (
        !auth.user ||
        this.workspaceInteractionLocked ||
        editVersionCommands.revertConfirmation ||
        this.navigation ||
        (target.kind === "work-order" &&
          target.workOrderId === workOrders.selectedWorkOrderId)
      )
        return null;
      const recovery = useWorkspaceRecoveryStore();
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
        void this.performNavigation(target);
        return null;
      }
      const id = crypto.randomUUID();
      this.navigation = {
        id,
        actorId: auth.user.id,
        sessionEpoch: auth.sessionEpoch,
        sourceKey: editVersionCommands.recoveryKey,
        target,
        phase: dirty ? "dirty" : sent ? "sent" : "stale",
        commandId: null,
      };
      this.navigationError = null;
      return id;
    },
    cancelNavigation(id: string): void {
      if (this.navigation?.id === id) this.navigation = null;
    },
    async prepareLogout(): Promise<boolean> {
      const auth = useAuthStore();
      const actor = auth.user?.id;
      if (!actor) return true;
      const sid = auth.sessionId;
      const epoch = auth.sessionEpoch;
      const recovery = useWorkspaceRecoveryStore();
      const ready = await recovery.prepareActorLogout(actor);
      if (auth.sessionId !== sid || auth.sessionEpoch !== epoch) return false;
      if (!ready) {
        this.navigationError =
          "Выход приостановлен: не удалось сохранить данные восстановления. Повторите попытку.";
        return false;
      }
      this.navigationError = null;
      return true;
    },
    async performNavigation(target: NavigationTarget): Promise<void> {
      const editorSession = useEditorSessionStore();
      const workOrders = useWorkOrdersStore();
      if (target.kind === "logout") {
        const auth = useAuthStore();
        if (this.logoutAttempt || !auth.sessionId) return;
        const attempt = {
          id: crypto.randomUUID(),
          sessionId: auth.sessionId,
          sessionEpoch: auth.sessionEpoch,
        };
        this.logoutAttempt = attempt;
        const isCurrent = () =>
          auth.sessionId === attempt.sessionId &&
          auth.sessionEpoch === attempt.sessionEpoch;
        try {
          if (!(await this.prepareLogout()) || !isCurrent()) return;
          const ended = await auth.logout();
          if (ended && isCurrent()) auth.clearLocalSession();
        } finally {
          if (this.logoutAttempt?.id === attempt.id) this.logoutAttempt = null;
        }
        return;
      }
      if (this.workspaceInteractionLocked) return;
      editorSession.clearOpenedWorkspace({ force: true });
      workOrders.selectWorkOrder(target.workOrderId);
    },
    async resolveNavigation(
      id: string,
      choice: NavigationChoice,
    ): Promise<void> {
      const editVersionCommands = useEditVersionCommandsStore();
      const editVersionDraft = useEditVersionDraftStore();
      const context = this.navigation,
        auth = useAuthStore();
      if (!context || context.id !== id || context.phase === "saving") return;
      if (
        context.actorId !== auth.user?.id ||
        context.sessionEpoch !== auth.sessionEpoch ||
        context.sourceKey !== editVersionCommands.recoveryKey
      ) {
        this.navigation = null;
        return;
      }
      if (choice === "stay") {
        this.navigation = null;
        return;
      }
      if (choice === "save" && context.phase === "dirty") {
        context.phase = "saving";
        await editVersionCommands.saveLocalDraft();
        if (this.navigation?.id === id && !this.navigation.commandId)
          this.navigation = null;
        return;
      }
      if (
        (choice === "discard" && context.phase === "dirty") ||
        (choice === "leave" && context.phase !== "dirty")
      ) {
        this.navigation = null;
        if (choice === "discard") editVersionDraft.cancelLocalEdit();
        await this.performNavigation(context.target);
      }
    },
    allowWorkspaceNavigation(): boolean {
      const editVersionDraft = useEditVersionDraftStore();
      if (this.canLeaveWorkspace) return true;
      editVersionDraft.editBlockReason = "FINISH_OR_CANCEL_LOCAL_WORK";
      return false;
    },
  },
});
