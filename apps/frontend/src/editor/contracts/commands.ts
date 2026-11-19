import type { WorkspaceCommandPhase } from "@/contracts/workspace/workspace-command";
import {
  type GeometrySaveResult,
  type LineStringXY,
  type PendingGeometryCommand,
  type WorkspaceRecoveryRecord,
} from "@/contracts/workspace/workspace-edit";
import {
  type RecoveryCompletion,
  type RecoverySource,
} from "@/contracts/workspace/workspace-recovery";
import type { SaveAttempt } from "@/editor/editorWorkflowContracts";
export type RevertConfirmationContext = {
  confirmationId: string;
  actorId: string;
  workOrderId: string;
  editVersionId: string;
  featureId: string;
  token: string;
  phase: "resolve-dirty" | "confirm";
};
export type EditVersionCommandsState = {
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
export type CommandsPort = Readonly<EditVersionCommandsState> & {
  captureSaveAttempt(attempt: SaveAttempt): void;
  readonly recoveryKey: string | null;
  readonly activeComparison:
    | EditVersionCommandsState["staleComparisons"][string]
    | null;
  readonly previewGeometry: LineStringXY | null;
  readonly recoveryRecord: WorkspaceRecoveryRecord | null;
  readonly phase: EditVersionCommandsState["localPhase"];
  readonly readbackError: string | null;
  readonly storageError: string | null;
  readonly canStartRevert: boolean;
  readonly canRetryPendingCommand: boolean;
  readonly canRetryCurrentRead: boolean;
  readonly canDiscardRejectedAttempt: boolean;
  readonly didSaveChangeGeometry: boolean | null;
  readonly pendingCommand: PendingGeometryCommand | null;
  showComparisonPreview(mode: "source" | "candidate" | "current"): boolean;
  hideComparisonPreview(): void;
  removeStaleComparison(key: string): void;
  finishLocalEditing(): void;
  resetForeground(clearResult: boolean): void;
  resetActorState(): void;
  beginRevert(): "resolve-dirty" | "confirm" | "blocked";
  isCurrentRevertConfirmation(id: string): boolean;
  cancelRevert(id: string): void;
  discardLocalDraftForRevert(id: string): boolean;
  confirmRevert(id: string): Promise<void>;
  attachRecoveryHost(): () => void;
  completeRecovery({ record, sessionEpoch }: RecoveryCompletion): void;
  suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void;
  suspendWorkOrderRecovery(workOrderId: string): Promise<void>;
  hasAccessSuspension(actorId: string): boolean;
  saveLocalDraft(): Promise<void>;
  refreshCurrentWorkspace(): Promise<void>;
  retryPendingSave(): Promise<void>;
  restorePendingSave(): Promise<void>;
  discardRejectedAttempt(): boolean;
  markLocalEditing(clearResult?: boolean): void;
  startRevertConfirmation(context: RevertConfirmationContext): void;
  finishRevertConfirmation(id: string): void;
  resolveRevertDraft(id: string): void;
  acceptRejectedRecovery(
    completion: RecoveryCompletion,
    selected: boolean,
  ): void;
  acceptSuccessfulRecovery(completion: RecoveryCompletion): void;
  reserveSubmission(): void;
  recordSubmission(commandId: string, source: LineStringXY): void;
  submissionBlocked(storageError: boolean): void;
  restoreStaleComparison(): void;
};
