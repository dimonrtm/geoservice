import type {
  NavigationChoice,
  NavigationContext,
  NavigationTarget,
} from "@/domain/workspace/workspaceNavigation";
import { type SaveAttempt } from "@/editor/editorWorkflowContracts";
export type EditorNavigationState = {
  navigation: NavigationContext | null;
  navigationError: string | null;
  logoutAttempt: { id: string; sessionId: string; sessionEpoch: number } | null;
};
export type NavigationPort = Readonly<EditorNavigationState> & {
  readonly workspaceInteractionLocked: boolean;
  readonly canLeaveWorkspace: boolean;
  beginNavigation(context: NavigationContext): boolean;
  bindNavigationSave(id: string, attempt: SaveAttempt): boolean;
  abortNavigation(id: string): void;
  takeCompletedNavigation(attempt: SaveAttempt): NavigationTarget | null;
  resetNavigationState(): void;
  requestNavigation(target: NavigationTarget): string | null;
  cancelNavigation(id: string): void;
  prepareLogout(): Promise<boolean>;
  performNavigation(target: NavigationTarget): Promise<void>;
  resolveNavigation(id: string, choice: NavigationChoice): Promise<void>;
  allowWorkspaceNavigation(): boolean;
  startNavigationSave(id: string): boolean;
  reportLogoutPreparation(ready: boolean): void;
  startLogoutAttempt(
    attempt: NonNullable<EditorNavigationState["logoutAttempt"]>,
  ): void;
  finishLogoutAttempt(id: string): void;
};
