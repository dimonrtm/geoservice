import type { ResetWorkOrdersOptions } from "@/stores/editor_session/editorSessionStorage";
import type {
  ClearOpenedWorkspaceOptions,
  EditorWorkflowPorts,
} from "./editorWorkflowPorts";
import { createCommandsWorkflow } from "./workflows/commandsWorkflow";
import { createDraftWorkflow } from "./workflows/draftWorkflow";
import { createNavigationWorkflow } from "./workflows/navigationWorkflow";

export function createEditorWorkflow(ports: EditorWorkflowPorts) {
  const draft = createDraftWorkflow(ports);
  const navigation = createNavigationWorkflow(ports);
  const commands = createCommandsWorkflow(ports);
  function clearOpenedWorkspace(
    options: ClearOpenedWorkspaceOptions = {},
  ): void {
    if (!options.force && !navigation.actions.allowWorkspaceNavigation())
      return;
    const pendingNavigation = ports.editorNavigation.navigation;
    if (
      pendingNavigation &&
      pendingNavigation.sourceKey === ports.editVersionCommands.recoveryKey
    )
      ports.editorNavigation.abortNavigation(pendingNavigation.id);
    ports.editorSession.closeWorkspaceState(options);
    ports.editVersionDraft.resetDraftState();
    ports.editVersionCommands.resetForeground(!!options.force);
    ports.editor.reset();
  }
  function resetEditor(options: ResetWorkOrdersOptions = {}): void {
    ports.editorSession.resetSessionState(options);
    ports.editVersionCommands.resetActorState();
    ports.editVersionDraft.resetDraftState();
    ports.editorNavigation.resetNavigationState();
    ports.editor.reset();
  }
  return {
    ...draft.actions,
    ...navigation.actions,
    ...commands.actions,
    clearOpenedWorkspace,
    resetEditor,
    draft: draft.actions,
    navigation: navigation.actions,
    commands: commands.actions,
    getters: {
      draft: draft.getters,
      navigation: navigation.getters,
      commands: commands.getters,
    },
  };
}
export type EditorWorkflow = ReturnType<typeof createEditorWorkflow>;
