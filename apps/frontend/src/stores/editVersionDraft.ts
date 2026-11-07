import { defineStore } from "pinia";
import {
  createLocalDraft,
  updateLocalVertex,
  isLocalDraftDirty,
  type WorkspaceLocalDraft,
} from "@/domain/workspaceDraft";
import { useAuthStore } from "./auth";

import { useEditVersionEditor } from "@/composables/useEditVersionEditor";
import { useEditVersionCommandsStore } from "@/stores/editVersionCommands";
import { useEditorNavigationStore } from "@/stores/editorNavigation";
import { useEditorSessionStore } from "@/stores/editorSession";
type EditVersionDraftState = {
  localDraft: WorkspaceLocalDraft | null;
  editBlockReason: string | null;
};

export const useEditVersionDraftStore = defineStore("editVersionDraft", {
  state: (): EditVersionDraftState => ({
    localDraft: null,
    editBlockReason: null,
  }),
  actions: {
    beginLocalEdit(featureId: string, vertexIndex: number): boolean {
      const editorNavigation = useEditorNavigationStore();
      const editorSession = useEditorSessionStore();
      const editVersionCommands = useEditVersionCommandsStore();
      if (
        !useEditVersionEditor().readyFor(featureId) ||
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
      if (this.localDraft) {
        if (
          this.localDraft.featureId === featureId &&
          this.localDraft.vertexIndex === vertexIndex
        )
          return true;
        if (isLocalDraftDirty(this.localDraft)) {
          this.editBlockReason = "FINISH_OR_CANCEL_LOCAL_WORK";
          return false;
        }
      }
      try {
        this.localDraft = createLocalDraft(
          editorSession.activeWorkspace,
          featureId,
          vertexIndex,
        );
        editVersionCommands.localPhase = "editing";
        this.editBlockReason = null;
        return true;
      } catch {
        this.editBlockReason = "INVALID_LOCAL_EDIT";
        return false;
      }
    },
    moveLocalVertex(xy: [number, number]): boolean {
      const editorNavigation = useEditorNavigationStore();
      const editVersionCommands = useEditVersionCommandsStore();
      if (
        editorNavigation.workspaceInteractionLocked ||
        !this.localDraft ||
        !useEditVersionEditor().readyFor(this.localDraft.featureId) ||
        editVersionCommands.storageError ||
        ["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
          editVersionCommands.saveError ?? "",
        ) ||
        editVersionCommands.recoveryRecord ||
        !["editing", "rejected"].includes(editVersionCommands.phase)
      )
        return false;
      try {
        this.localDraft = updateLocalVertex(this.localDraft, xy);
        editVersionCommands.localPhase = "editing";
        return true;
      } catch {
        this.editBlockReason = "INVALID_LOCAL_EDIT";
        return false;
      }
    },
    cancelLocalEdit(): boolean {
      const editorNavigation = useEditorNavigationStore();
      const editVersionCommands = useEditVersionCommandsStore();
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
        delete editVersionCommands.staleComparisons[
          editVersionCommands.recoveryKey
        ];
      editVersionCommands.comparisonPreview = null;
      this.localDraft = null;
      editVersionCommands.rejectedCandidateGeometry = null;
      editVersionCommands.saveError = null;
      editVersionCommands.localPhase = "idle";
      this.editBlockReason = null;
      return true;
    },
    discardLocalChangesKeepingSelection(): boolean {
      const editorNavigation = useEditorNavigationStore();
      const editVersionCommands = useEditVersionCommandsStore();
      const editorSession = useEditorSessionStore();
      const auth = useAuthStore();
      if (
        editorNavigation.workspaceInteractionLocked ||
        !auth.isAuthenticated ||
        auth.user?.role !== "editor" ||
        editVersionCommands.hasAccessSuspension(auth.user.id) ||
        !editorSession.activeWorkspace ||
        !this.localDraft ||
        !isLocalDraftDirty(this.localDraft) ||
        editVersionCommands.recoveryRecord ||
        editVersionCommands.storageError ||
        !["editing", "rejected"].includes(editVersionCommands.phase)
      )
        return false;
      const draft = createLocalDraft(
        editorSession.activeWorkspace,
        this.localDraft.featureId,
        this.localDraft.vertexIndex,
      );
      this.localDraft = draft;
      editVersionCommands.localPhase = "editing";
      editVersionCommands.saveError = null;
      this.editBlockReason = null;
      editVersionCommands.commandResult = null;
      editVersionCommands.submittedSourceGeometry = null;
      editVersionCommands.submittedCommandId = null;
      editVersionCommands.rejectedCandidateGeometry = null;
      return true;
    },
  },
});
