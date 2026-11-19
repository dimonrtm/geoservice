import type { WorkspaceCommandPhase } from "@/contracts/workspace/workspace-command";
import {
  copyGeometry,
  type GeometrySaveResult,
  type LineStringXY,
  type PendingGeometryCommand,
  type WorkspaceRecoveryRecord,
} from "@/contracts/workspace/workspace-edit";
import {
  type RecoveryCompletion,
  type RecoverySource,
} from "@/contracts/workspace/workspace-recovery";
import { requireEditorWorkflow } from "@/editor/editorRuntimeBinding";
import type { SaveAttempt } from "@/editor/editorWorkflowContracts";
import { defineStore } from "pinia";

type RevertConfirmationContext = {
  confirmationId: string;
  actorId: string;
  workOrderId: string;
  editVersionId: string;
  featureId: string;
  token: string;
  phase: "resolve-dirty" | "confirm";
};
type EditVersionCommandsState = {
  activeSaveAttempt: SaveAttempt | null;
  comparisonPreview: "source" | "candidate" | "current" | null;
  staleComparisons: Record<
    string,
    {
      source: RecoverySource;
      candidate: LineStringXY;
      commandId: string;
      featureId: string;
    }
  >;
  revertConfirmation: RevertConfirmationContext | null;
  recoveryReadSeq: number | null;
  submittedSourceGeometry: LineStringXY | null;
  submittedCommandId: string | null;
  rejectedCandidateGeometry: LineStringXY | null;
  saveError: string | null;
  commandResult: GeometrySaveResult | null;
  localPhase: WorkspaceCommandPhase;
};
export const useEditVersionCommandsStore = defineStore("editVersionCommands", {
  state: (): EditVersionCommandsState => ({
    activeSaveAttempt: null,
    comparisonPreview: null,
    staleComparisons: {},
    revertConfirmation: null,
    recoveryReadSeq: null,
    submittedSourceGeometry: null,
    submittedCommandId: null,
    rejectedCandidateGeometry: null,
    saveError: null,
    commandResult: null,
    localPhase: "idle",
  }),
  getters: {
    recoveryKey(): string | null {
      return requireEditorWorkflow(this).getters.commands.recoveryKey();
    },
    activeComparison():
      | EditVersionCommandsState["staleComparisons"][string]
      | null {
      return requireEditorWorkflow(this).getters.commands.activeComparison();
    },
    previewGeometry(): LineStringXY | null {
      return requireEditorWorkflow(this).getters.commands.previewGeometry();
    },
    recoveryRecord(): WorkspaceRecoveryRecord | null {
      return requireEditorWorkflow(this).getters.commands.recoveryRecord();
    },
    phase(): EditVersionCommandsState["localPhase"] {
      return requireEditorWorkflow(this).getters.commands.phase();
    },
    readbackError(): string | null {
      return requireEditorWorkflow(this).getters.commands.readbackError();
    },
    storageError(): string | null {
      return requireEditorWorkflow(this).getters.commands.storageError();
    },
    canStartRevert(): boolean {
      return requireEditorWorkflow(this).getters.commands.canStartRevert();
    },
    canRetryPendingCommand(): boolean {
      return requireEditorWorkflow(
        this,
      ).getters.commands.canRetryPendingCommand();
    },
    canRetryCurrentRead(): boolean {
      return requireEditorWorkflow(this).getters.commands.canRetryCurrentRead();
    },
    canDiscardRejectedAttempt(): boolean {
      return requireEditorWorkflow(
        this,
      ).getters.commands.canDiscardRejectedAttempt();
    },
    didSaveChangeGeometry(): boolean | null {
      return requireEditorWorkflow(
        this,
      ).getters.commands.didSaveChangeGeometry();
    },
    pendingCommand(): PendingGeometryCommand | null {
      return requireEditorWorkflow(this).getters.commands.pendingCommand();
    },
  },
  actions: {
    captureSaveAttempt(attempt: SaveAttempt): void {
      this.activeSaveAttempt = attempt;
    },

    markLocalEditing(clearResult = false): void {
      this.localPhase = "editing";
      if (clearResult) {
        this.resetForeground(true);
        this.localPhase = "editing";
      }
    },
    startRevertConfirmation(context: RevertConfirmationContext): void {
      this.revertConfirmation = context;
    },
    finishRevertConfirmation(id: string): void {
      if (this.revertConfirmation?.confirmationId === id)
        this.revertConfirmation = null;
    },
    resolveRevertDraft(id: string): void {
      if (this.revertConfirmation?.confirmationId === id)
        this.revertConfirmation.phase = "confirm";
    },
    acceptRejectedRecovery(
      completion: RecoveryCompletion,
      selected: boolean,
    ): void {
      const { record } = completion;
      if (record.outcome.kind !== "rejected") return;
      if (record.outcome.error.code === "DRAFT_VERSION_STALE")
        this.staleComparisons[record.key] = {
          source: record.source,
          candidate: copyGeometry(record.command.request.geometry),
          commandId: record.command.request.commandId,
          featureId: record.command.target.featureId,
        };
      if (selected) {
        this.saveError = record.outcome.error.code;
        this.rejectedCandidateGeometry = copyGeometry(
          record.command.request.geometry,
        );
        this.localPhase =
          record.outcome.error.code === "DRAFT_VERSION_STALE"
            ? "stale"
            : "rejected";
      }
    },
    acceptSuccessfulRecovery(completion: RecoveryCompletion): void {
      const { record } = completion;
      if (record.outcome.kind !== "succeeded") return;
      this.commandResult = record.outcome.result;
      this.submittedSourceGeometry = record.source?.geometry ?? null;
      this.submittedCommandId = record.command.request.commandId;
      this.finishLocalEditing();
    },
    reserveSubmission(): void {
      this.localPhase = "sending";
    },
    recordSubmission(commandId: string, source: LineStringXY): void {
      this.submittedSourceGeometry = source;
      this.submittedCommandId = commandId;
      this.commandResult = null;
      this.saveError = null;
      this.rejectedCandidateGeometry = null;
    },
    submissionBlocked(storageError: boolean): void {
      this.localPhase = storageError ? "blocked" : "editing";
    },
    restoreStaleComparison(): void {
      this.localPhase = "stale";
      this.saveError = "DRAFT_VERSION_STALE";
    },
    showComparisonPreview(mode: "source" | "candidate" | "current"): boolean {
      const comparison = this.activeComparison;
      if (!comparison || (mode === "source" && !comparison.source))
        return false;
      this.comparisonPreview = mode;
      return true;
    },
    hideComparisonPreview(): void {
      this.comparisonPreview = null;
    },
    removeStaleComparison(key: string): void {
      delete this.staleComparisons[key];
    },
    finishLocalEditing(): void {
      this.rejectedCandidateGeometry = null;
      this.saveError = null;
      this.localPhase = "idle";
    },
    resetForeground(clearResult: boolean): void {
      this.comparisonPreview = null;
      this.submittedSourceGeometry = null;
      this.submittedCommandId = null;
      this.finishLocalEditing();
      if (clearResult) this.commandResult = null;
    },
    resetActorState(): void {
      if (this.revertConfirmation)
        this.cancelRevert(this.revertConfirmation.confirmationId);
      this.$reset();
    },
    beginRevert(): "resolve-dirty" | "confirm" | "blocked" {
      return requireEditorWorkflow(this).commands.beginRevert();
    },
    isCurrentRevertConfirmation(id: string): boolean {
      return requireEditorWorkflow(this).commands.isCurrentRevertConfirmation(
        id,
      );
    },
    cancelRevert(id: string): void {
      return requireEditorWorkflow(this).commands.cancelRevert(id);
    },
    discardLocalDraftForRevert(id: string): boolean {
      return requireEditorWorkflow(this).commands.discardLocalDraftForRevert(
        id,
      );
    },
    confirmRevert(id: string): Promise<void> {
      return requireEditorWorkflow(this).commands.confirmRevert(id);
    },
    attachRecoveryHost(): () => void {
      return requireEditorWorkflow(this).commands.attachRecoveryHost();
    },
    completeRecovery({ record, sessionEpoch }: RecoveryCompletion): void {
      return requireEditorWorkflow(this).commands.completeRecovery({
        record,
        sessionEpoch,
      });
    },
    suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void {
      return requireEditorWorkflow(
        this,
      ).commands.suspendWorkspaceRecoveryForAccessLoss(actorId);
    },
    suspendWorkOrderRecovery(workOrderId: string): Promise<void> {
      return requireEditorWorkflow(this).commands.suspendWorkOrderRecovery(
        workOrderId,
      );
    },
    hasAccessSuspension(actorId: string): boolean {
      return requireEditorWorkflow(this).commands.hasAccessSuspension(actorId);
    },
    async saveLocalDraft(): Promise<void> {
      await requireEditorWorkflow(this).commands.saveLocalDraft();
    },
    refreshCurrentWorkspace(): Promise<void> {
      return requireEditorWorkflow(this).commands.refreshCurrentWorkspace();
    },
    retryPendingSave(): Promise<void> {
      return requireEditorWorkflow(this).commands.retryPendingSave();
    },
    restorePendingSave(): Promise<void> {
      return requireEditorWorkflow(this).commands.restorePendingSave();
    },
    discardRejectedAttempt(): boolean {
      return requireEditorWorkflow(this).commands.discardRejectedAttempt();
    },
  },
});
