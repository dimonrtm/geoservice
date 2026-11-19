import { type WorkspaceLocalDraft } from "@/domain/workspace/workspaceDraft";
import {
  type DraftIdentity,
  type EditorContext,
} from "@/editor/editorWorkflowContracts";
export type EditVersionDraftState = {
  draftIdentity: DraftIdentity | null;
  localDraft: WorkspaceLocalDraft | null;
  editBlockReason: string | null;
};
export type DraftPort = Readonly<EditVersionDraftState> & {
  startDraft(identity: DraftIdentity, draft: WorkspaceLocalDraft): void;
  updateDraft(identity: DraftIdentity, xy: [number, number]): boolean;
  finishDraft(identity: DraftIdentity): boolean;
  clearDraftForContext(context: EditorContext): boolean;
  reportEditBlocked(reason: string | null): void;
  beginLocalEdit(featureId: string, vertexIndex: number): boolean;
  moveLocalVertex(xy: [number, number]): boolean;
  cancelLocalEdit(): boolean;
  discardLocalChangesKeepingSelection(): boolean;
  resetDraftState(): void;
  replaceDraft(draft: WorkspaceLocalDraft, context: EditorContext | null): void;
  moveDraftVertex(xy: [number, number]): void;
};
