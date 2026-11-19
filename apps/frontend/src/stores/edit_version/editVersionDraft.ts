import {
  updateLocalVertex,
  type WorkspaceLocalDraft,
} from "@/domain/workspace/workspaceDraft";
import { requireEditorWorkflow } from "@/editor/editorRuntimeBinding";
import {
  sameDraft,
  sameEditorContext,
  type DraftIdentity,
  type EditorContext,
} from "@/editor/editorWorkflowContracts";
import { defineStore } from "pinia";

type EditVersionDraftState = {
  draftGeneration: number;
  draftIdentity: DraftIdentity | null;
  localDraft: WorkspaceLocalDraft | null;
  editBlockReason: string | null;
};
export const useEditVersionDraftStore = defineStore("editVersionDraft", {
  state: (): EditVersionDraftState => ({
    draftGeneration: 0,
    draftIdentity: null,
    localDraft: null,
    editBlockReason: null,
  }),
  getters: {},
  actions: {
    resetDraftState(): void {
      this.localDraft = null;
      this.draftIdentity = null;
      this.editBlockReason = null;
    },
    replaceDraft(
      draft: WorkspaceLocalDraft,
      context: EditorContext | null,
    ): void {
      const generation = ++this.draftGeneration;
      this.localDraft = draft;
      this.draftIdentity = context
        ? { ...context, draftGeneration: generation }
        : null;
      this.editBlockReason = null;
    },
    moveDraftVertex(xy: [number, number]): void {
      if (this.localDraft)
        this.localDraft = updateLocalVertex(this.localDraft, xy);
    },
    startDraft(identity: DraftIdentity, draft: WorkspaceLocalDraft): void {
      this.draftGeneration = Math.max(
        this.draftGeneration,
        identity.draftGeneration,
      );
      this.draftIdentity = { ...identity };
      this.localDraft = draft;
      this.editBlockReason = null;
    },
    updateDraft(identity: DraftIdentity, xy: [number, number]): boolean {
      if (!sameDraft(this.draftIdentity, identity) || !this.localDraft)
        return false;
      this.localDraft = updateLocalVertex(this.localDraft, xy);
      return true;
    },
    finishDraft(identity: DraftIdentity): boolean {
      if (!sameDraft(this.draftIdentity, identity)) return false;
      this.localDraft = null;
      this.draftIdentity = null;
      return true;
    },
    clearDraftForContext(context: EditorContext): boolean {
      if (
        !this.draftIdentity ||
        !sameEditorContext(this.draftIdentity, context)
      )
        return false;
      this.localDraft = null;
      this.draftIdentity = null;
      return true;
    },
    reportEditBlocked(reason: string | null): void {
      this.editBlockReason = reason;
    },
    beginLocalEdit(featureId: string, vertexIndex: number): boolean {
      return requireEditorWorkflow(this).draft.beginLocalEdit(
        featureId,
        vertexIndex,
      );
    },
    moveLocalVertex(xy: [number, number]): boolean {
      return requireEditorWorkflow(this).draft.moveLocalVertex(xy);
    },
    cancelLocalEdit(): boolean {
      return requireEditorWorkflow(this).draft.cancelLocalEdit();
    },
    discardLocalChangesKeepingSelection(): boolean {
      return requireEditorWorkflow(
        this,
      ).draft.discardLocalChangesKeepingSelection();
    },
  },
});
