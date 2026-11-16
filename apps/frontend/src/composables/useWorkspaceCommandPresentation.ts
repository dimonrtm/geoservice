import { useEditVersionEditor } from "@/composables/edit_version/useEditVersionEditor";
import { useEditorSessionStore } from "@/stores/editor_session/editorSession";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { useEditVersionCommandsStore } from "@/stores/edit_version/editVersionCommands";
import { useEditorNavigationStore } from "@/stores/editor_navigation/editorNavigation";
import { computed, type ComputedRef } from "vue";
import {
  presentWorkspaceCommands,
  type WorkspaceCommandPresentation,
  type WorkspaceCommandState,
} from "@/domain/workspace/workspaceCommandPresentation";

export function useWorkspaceCommandPresentation(
  actorCanEdit: () => boolean,
): ComputedRef<WorkspaceCommandPresentation> {
  const editorSession = useEditorSessionStore();
  const editVersionDraft = useEditVersionDraftStore();
  const editVersionCommands = useEditVersionCommandsStore();
  const editorNavigation = useEditorNavigationStore();
  const editor = useEditVersionEditor();
  return computed(() => {
    const state = collectState();
    return presentWorkspaceCommands(state, actorCanEdit());
  });
  function collectState(): WorkspaceCommandState {
    const changedFeature =
      editorSession.activeWorkspace?.workOrder.editVersion.changeSet?.featureId;
    return {
      revertBaselineReady: !!changedFeature && editor.readyFor(changedFeature),
      draftBaselineReady:
        !!editVersionDraft.localDraft &&
        editor.readyFor(editVersionDraft.localDraft.featureId),
      activeWorkspace: editorSession.activeWorkspace,
      localDraft: editVersionDraft.localDraft,
      phase: editVersionCommands.phase,
      recoveryRecord: editVersionCommands.recoveryRecord,
      commandResult: editVersionCommands.commandResult,
      saveError: editVersionCommands.saveError,
      readbackError: editVersionCommands.readbackError,
      storageError: editVersionCommands.storageError,
      didSaveChangeGeometry: editVersionCommands.didSaveChangeGeometry,
      rejectedCandidateGeometry: editVersionCommands.rejectedCandidateGeometry,
      canRetryPendingCommand: editVersionCommands.canRetryPendingCommand,
      canRetryCurrentRead: editVersionCommands.canRetryCurrentRead,
      canDiscardRejectedAttempt: editVersionCommands.canDiscardRejectedAttempt,
      workspaceInteractionLocked: editorNavigation.workspaceInteractionLocked,
    };
  }
}
