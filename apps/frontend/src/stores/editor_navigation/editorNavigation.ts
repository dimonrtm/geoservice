import type {
  NavigationChoice,
  NavigationContext,
  NavigationTarget,
} from "@/domain/workspace/workspaceNavigation";
import { requireEditorWorkflow } from "@/editor/editorRuntimeBinding";
import {
  matchesNavigation,
  type SaveAttempt,
} from "@/editor/editorWorkflowContracts";
import { defineStore } from "pinia";

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
    workspaceInteractionLocked(): boolean {
      return requireEditorWorkflow(
        this,
      ).getters.navigation.workspaceInteractionLocked();
    },
    canLeaveWorkspace(): boolean {
      return requireEditorWorkflow(this).getters.navigation.canLeaveWorkspace();
    },
  },
  actions: {
    startNavigationSave(id: string): boolean {
      if (this.navigation?.id !== id || this.navigation.phase !== "dirty")
        return false;
      this.navigation.phase = "saving";
      return true;
    },
    reportLogoutPreparation(ready: boolean): void {
      this.navigationError = ready
        ? null
        : "Выход приостановлен: не удалось сохранить данные восстановления. Повторите попытку.";
    },
    startLogoutAttempt(
      attempt: NonNullable<EditorNavigationState["logoutAttempt"]>,
    ): void {
      this.logoutAttempt = attempt;
    },
    finishLogoutAttempt(id: string): void {
      if (this.logoutAttempt?.id === id) this.logoutAttempt = null;
    },
    beginNavigation(context: NavigationContext): boolean {
      if (this.navigation) return false;
      this.navigation = { ...context };
      this.navigationError = null;
      return true;
    },
    bindNavigationSave(id: string, attempt: SaveAttempt): boolean {
      const context = this.navigation;
      if (
        !context ||
        context.id !== id ||
        !matchesNavigation(context, attempt) ||
        !["dirty", "saving"].includes(context.phase) ||
        context.commandId
      )
        return false;
      context.phase = "saving";
      context.commandId = attempt.commandId;
      return true;
    },
    abortNavigation(id: string): void {
      if (this.navigation?.id === id) this.navigation = null;
    },
    takeCompletedNavigation(attempt: SaveAttempt): NavigationTarget | null {
      const context = this.navigation;
      if (
        !context ||
        context.phase !== "saving" ||
        !matchesNavigation(context, attempt) ||
        context.commandId !== attempt.commandId
      )
        return null;
      this.navigation = null;
      return context.target;
    },
    resetNavigationState(): void {
      this.$reset();
    },
    requestNavigation(target: NavigationTarget): string | null {
      return requireEditorWorkflow(this).navigation.requestNavigation(target);
    },
    cancelNavigation(id: string): void {
      return requireEditorWorkflow(this).navigation.cancelNavigation(id);
    },
    prepareLogout(): Promise<boolean> {
      return requireEditorWorkflow(this).navigation.prepareLogout();
    },
    performNavigation(target: NavigationTarget): Promise<void> {
      return requireEditorWorkflow(this).navigation.performNavigation(target);
    },
    resolveNavigation(id: string, choice: NavigationChoice): Promise<void> {
      return requireEditorWorkflow(this).navigation.resolveNavigation(
        id,
        choice,
      );
    },
    allowWorkspaceNavigation(): boolean {
      return requireEditorWorkflow(this).navigation.allowWorkspaceNavigation();
    },
  },
});
