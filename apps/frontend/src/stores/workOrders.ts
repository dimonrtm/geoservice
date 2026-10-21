import { defineStore } from "pinia";
import { watch, type WatchStopHandle } from "vue";
import {
  createLocalDraft,
  updateLocalVertex,
  isLocalDraftDirty,
  type WorkspaceLocalDraft,
} from "@/domain/workspaceDraft";
import {
  copyGeometry,
  freezePendingCommand,
  parseGeometrySaveResult,
  parseWorkspaceResponse,
  type GeometrySaveResult,
  type WorkspaceRecoveryRecord,
  type PendingGeometryCommand,
  type LineStringXY,
  isLineStringXY,
} from "@/contracts/workspace-edit";
import { useAuthStore } from "./auth";
import {
  readRecoveryRecord,
  writeRecoveryRecord,
  removeRecoveryRecord,
  blockStoredRecoveriesForAccessLoss,
} from "./workspaceRecoveryStorage";
import { classifySaveFailure } from "./workspaceSaveErrors";
import { AUTO_RETRY_DELAYS_MS, waitForRetry } from "./workspaceRetry";

const retryControllers = new WeakMap<object, AbortController>();
const confirmationWatchers = new WeakMap<object, WatchStopHandle>();
const accessSuspensions = new WeakMap<
  object,
  Map<string, WorkspaceRecoveryRecord | null>
>();

import {
  fetchAssignedWorkOrders,
  fetchWorkspace,
  openEditVersion,
  saveFeatureGeometry,
} from "@/api/workOrders";
import { parseApiError } from "@/api/parseApiError";
import type { ErrorPresentation, ParsedApiError } from "@/contracts/api-error";
import type {
  WorkOrderStatus,
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";
import {
  presentWorkOrdersLoadError,
  presentWorkspaceOpenError,
  presentWorkspaceRestoreError,
} from "@/errors/apiErrorPresentations";

type WorkspaceErrorOperation = "open" | "restore";

type ClearOpenedWorkspaceOptions = {
  preserveStoredWorkspace?: boolean;
  force?: boolean;
};

type RevertConfirmationContext = {
  confirmationId: string;
  actorId: string;
  workOrderId: string;
  editVersionId: string;
  featureId: string;
  token: string;
  phase: "resolve-dirty" | "confirm";
};
type WorkOrdersState = {
  revertConfirmation: RevertConfirmationContext | null;
  recoveryReadSeq: number | null;
  submittedSourceGeometry: LineStringXY | null;
  submittedCommandId: string | null;
  rejectedCandidateGeometry: LineStringXY | null;
  recoveryRecord: WorkspaceRecoveryRecord | null;
  editRequestSeq: number;
  saveError: string | null;
  readbackError: string | null;
  storageError: string | null;
  localDraft: WorkspaceLocalDraft | null;
  commandResult: GeometrySaveResult | null;
  phase:
    | "idle"
    | "editing"
    | "sending"
    | "retry-wait"
    | "unknown"
    | "reading-current"
    | "rejected"
    | "stale"
    | "blocked";
  editBlockReason: string | null;
  items: WorkOrderSummary[];
  isLoading: boolean;
  loadError: ErrorPresentation | null;
  selectedWorkOrderId: string | null;
  openedWorkOrderId: string | null;
  openedEditVersionId: string | null;
  workspace: WorkspaceResponse | null;
  openingWorkOrderId: string | null;
  openingWorkspaceRequestSeq: number | null;
  openWorkspaceErrorByWorkOrderId: Record<
    string,
    ErrorPresentation | undefined
  >;
  openWorkspaceErrorOperationByWorkOrderId: Record<
    string,
    WorkspaceErrorOperation | undefined
  >;
  lastFittedWorkspaceKey: string | null;
  loadAssignedRequestSeq: number;
  openWorkspaceRequestSeq: number;
};

type StoredOpenedWorkspace = {
  workOrderId: string;
  editVersionId: string;
};

type StoredSelectedWorkOrder = {
  workOrderId: string;
};

export type ResetWorkOrdersOptions = {
  preserveOpenedWorkspace?: boolean;
  preserveSelectedWorkOrder?: boolean;
};

const SELECTED_WORK_ORDER_STORAGE_KEY = "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";

function sessionStorageOrNull(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function readStoredOpenedWorkspace(): StoredOpenedWorkspace | null {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(OPENED_WORKSPACE_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<StoredOpenedWorkspace>;
    if (
      typeof parsed.workOrderId !== "string" ||
      typeof parsed.editVersionId !== "string"
    ) {
      clearStoredOpenedWorkspace();
      return null;
    }

    return {
      workOrderId: parsed.workOrderId,
      editVersionId: parsed.editVersionId,
    };
  } catch {
    clearStoredOpenedWorkspace();
    return null;
  }
}

function storeOpenedWorkspace(openedWorkspace: StoredOpenedWorkspace): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify(openedWorkspace),
    );
  } catch {
    // The in-memory workspace remains valid even if browser storage is unavailable.
  }
}

function clearStoredOpenedWorkspace(): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(OPENED_WORKSPACE_STORAGE_KEY);
  } catch {
    // Nothing to clean up if browser storage is unavailable.
  }
}

function clearStoredSelectedWorkOrder(): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(SELECTED_WORK_ORDER_STORAGE_KEY);
  } catch {
    // Nothing to clean up if browser storage is unavailable.
  }
}

function readStoredSelectedWorkOrder(): StoredSelectedWorkOrder | null {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<StoredSelectedWorkOrder>;
    if (
      typeof parsed.workOrderId !== "string" ||
      parsed.workOrderId.trim().length === 0
    ) {
      clearStoredSelectedWorkOrder();
      return null;
    }

    return { workOrderId: parsed.workOrderId };
  } catch {
    clearStoredSelectedWorkOrder();
    return null;
  }
}

function storeSelectedWorkOrder(workOrderId: string): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId }),
    );
  } catch {
    // The in-memory selection remains valid if browser storage is unavailable.
  }
}

function shouldPreserveStoredWorkspace(error: ParsedApiError): boolean {
  return (
    error.kind === "network" ||
    error.kind === "timeout" ||
    ((error.kind === "api" || error.kind === "http") && error.status >= 500)
  );
}

function isWorkspaceAccessFailure(error: ParsedApiError): boolean {
  return (
    (error.kind === "api" || error.kind === "http") &&
    [401, 403, 404, 409].includes(error.status)
  );
}

function createInitialWorkOrdersState(): WorkOrdersState {
  return {
    revertConfirmation: null,
    recoveryReadSeq: null,
    submittedSourceGeometry: null,
    submittedCommandId: null,
    rejectedCandidateGeometry: null,
    recoveryRecord: null,
    editRequestSeq: 0,
    saveError: null,
    readbackError: null,
    storageError: null,
    localDraft: null,
    commandResult: null,
    phase: "idle",
    editBlockReason: null,
    items: [],
    isLoading: false,
    loadError: null,
    selectedWorkOrderId: null,
    openedWorkOrderId: null,
    openedEditVersionId: null,
    workspace: null,
    openingWorkOrderId: null,
    openingWorkspaceRequestSeq: null,
    openWorkspaceErrorByWorkOrderId: {},
    openWorkspaceErrorOperationByWorkOrderId: {},
    lastFittedWorkspaceKey: null,
    loadAssignedRequestSeq: 0,
    openWorkspaceRequestSeq: 0,
  };
}

export const useWorkOrdersStore = defineStore("workOrders", {
  state: createInitialWorkOrdersState,
  getters: {
    workspaceInteractionLocked: (state): boolean =>
      state.revertConfirmation !== null,
    canStartRevert(): boolean {
      const auth = useAuthStore();
      return (
        auth.isAuthenticated &&
        auth.user?.role === "editor" &&
        !!this.activeWorkspace?.workOrder.editVersion.changeSet &&
        this.activeWorkspace.workOrder.editVersion.hasPersistedChangeSet &&
        !this.storageError &&
        !this.recoveryRecord &&
        !["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
          this.saveError ?? "",
        ) &&
        ["idle", "editing", "rejected"].includes(this.phase)
      );
    },
    canRetryPendingCommand(): boolean {
      const auth = useAuthStore();
      return (
        auth.isAuthenticated &&
        auth.user?.role === "editor" &&
        !!this.activeWorkspace &&
        !this.storageError &&
        this.phase === "unknown" &&
        this.recoveryRecord?.state === "unknown" &&
        this.recoveryRecord.command.actorId === auth.user.id
      );
    },
    canRetryCurrentRead(): boolean {
      const auth = useAuthStore();
      return (
        auth.isAuthenticated &&
        auth.user?.role === "editor" &&
        !!this.activeWorkspace &&
        !this.storageError &&
        !!this.readbackError &&
        this.recoveryReadSeq === null &&
        this.phase !== "blocked" &&
        (this.recoveryRecord?.state === "succeeded" ||
          this.recoveryRecord?.state === "rejected") &&
        this.recoveryRecord.command.actorId === auth.user.id
      );
    },
    canDiscardRejectedAttempt(): boolean {
      const auth = useAuthStore();
      return (
        auth.isAuthenticated &&
        auth.user?.role === "editor" &&
        !!this.activeWorkspace &&
        this.phase === "stale" &&
        !this.recoveryRecord &&
        !this.storageError &&
        !this.readbackError
      );
    },
    didSaveChangeGeometry: (state): boolean | null => {
      if (
        !state.commandResult ||
        !state.submittedSourceGeometry ||
        state.commandResult.commandId !== state.submittedCommandId
      )
        return null;
      return (
        JSON.stringify(
          state.commandResult.updatedFeature.geometry.coordinates,
        ) !== JSON.stringify(state.submittedSourceGeometry.coordinates)
      );
    },
    pendingCommand: (state): PendingGeometryCommand | null =>
      state.recoveryRecord?.command ?? null,
    canLeaveWorkspace: (state): boolean =>
      state.revertConfirmation === null &&
      state.localDraft === null &&
      state.recoveryRecord === null &&
      state.phase !== "reading-current" &&
      state.phase !== "blocked",
    isOpeningWorkspace: (state) => state.openingWorkOrderId !== null,
    selectedWorkOrder: (state) =>
      state.items.find((item) => item.id === state.selectedWorkOrderId) ?? null,
    activeWorkspace: (state) => {
      if (
        !state.workspace ||
        state.selectedWorkOrderId === null ||
        state.openedWorkOrderId !== state.selectedWorkOrderId
      ) {
        return null;
      }
      return state.workspace;
    },
    activeWorkspaceKey: (state) => {
      if (
        state.selectedWorkOrderId === null ||
        state.openedWorkOrderId !== state.selectedWorkOrderId ||
        state.openedEditVersionId === null
      ) {
        return null;
      }
      return `${state.openedWorkOrderId}:${state.openedEditVersionId}`;
    },
    selectedOpenWorkspaceError: (state) => {
      if (!state.selectedWorkOrderId) {
        return null;
      }
      return (
        state.openWorkspaceErrorByWorkOrderId[state.selectedWorkOrderId] ?? null
      );
    },
    selectedOpenWorkspaceErrorOperation: (state) => {
      if (!state.selectedWorkOrderId) {
        return null;
      }
      return (
        state.openWorkspaceErrorOperationByWorkOrderId[
          state.selectedWorkOrderId
        ] ?? null
      );
    },
  },
  actions: {
    beginRevert(): "resolve-dirty" | "confirm" | "blocked" {
      const auth = useAuthStore();
      if (
        !this.canStartRevert ||
        this.revertConfirmation ||
        !auth.user ||
        this.hasAccessSuspension(auth.user.id)
      )
        return "blocked";
      if (readRecoveryRecord(auth.user.id).kind !== "empty") {
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_REQUIRED";
        return "blocked";
      }
      const workspace = this.activeWorkspace!;
      const version = workspace.workOrder.editVersion;
      const phase =
        this.localDraft && isLocalDraftDirty(this.localDraft)
          ? "resolve-dirty"
          : "confirm";
      const confirmationId = crypto.randomUUID();
      this.revertConfirmation = {
        confirmationId,
        actorId: auth.user.id,
        workOrderId: workspace.workOrder.id,
        editVersionId: version.id,
        featureId: version.changeSet!.featureId,
        token: version.draftVersionToken,
        phase,
      };
      confirmationWatchers.get(this)?.();
      confirmationWatchers.set(
        this,
        watch(
          () => this.isCurrentRevertConfirmation(confirmationId),
          (valid) => {
            if (!valid) this.cancelRevert(confirmationId);
          },
          { flush: "sync" },
        ),
      );
      return phase;
    },
    isCurrentRevertConfirmation(id: string): boolean {
      const context = this.revertConfirmation;
      const auth = useAuthStore();
      const workspace = this.activeWorkspace;
      return (
        !!context &&
        context.confirmationId === id &&
        this.canStartRevert &&
        auth.user?.id === context.actorId &&
        workspace?.workOrder.id === context.workOrderId &&
        workspace.workOrder.editVersion.id === context.editVersionId &&
        this.openedEditVersionId === context.editVersionId &&
        workspace.workOrder.editVersion.draftVersionToken === context.token &&
        workspace.workOrder.editVersion.changeSet?.featureId ===
          context.featureId
      );
    },
    cancelRevert(id: string): void {
      if (this.revertConfirmation?.confirmationId !== id) return;
      confirmationWatchers.get(this)?.();
      confirmationWatchers.delete(this);
      this.revertConfirmation = null;
    },
    discardLocalDraftForRevert(id: string): boolean {
      if (
        !this.isCurrentRevertConfirmation(id) ||
        this.revertConfirmation?.phase !== "resolve-dirty"
      )
        return false;
      this.localDraft = null;
      this.rejectedCandidateGeometry = null;
      this.saveError = null;
      this.editBlockReason = null;
      this.phase = "idle";
      this.revertConfirmation.phase = "confirm";
      return true;
    },
    async confirmRevert(id: string): Promise<void> {
      if (
        !this.isCurrentRevertConfirmation(id) ||
        this.revertConfirmation?.phase !== "confirm"
      )
        return;
      const context = this.revertConfirmation;
      if (this.hasAccessSuspension(context.actorId)) return;
      if (readRecoveryRecord(context.actorId).kind !== "empty") {
        this.cancelRevert(id);
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_REQUIRED";
        return;
      }
      const command: PendingGeometryCommand = {
        actorId: context.actorId,
        target: {
          workOrderId: context.workOrderId,
          editVersionId: context.editVersionId,
          featureId: context.featureId,
        },
        request: {
          commandId: crypto.randomUUID(),
          draftVersionToken: context.token,
          geometry: copyGeometry(
            this.activeWorkspace!.workOrder.editVersion.changeSet!
              .baselineGeometry,
          ),
        },
      };
      this.cancelRevert(id);
      await submitGeometryCommand(this, command);
    },
    suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void {
      retryControllers.get(this)?.abort();
      retryControllers.delete(this);
      this.editRequestSeq += 1;
      this.openWorkspaceRequestSeq += 1;
      const actor =
        actorId ?? this.pendingCommand?.actorId ?? useAuthStore().user?.id;
      const hasRecovery =
        this.recoveryRecord !== null ||
        (actor !== undefined && readRecoveryRecord(actor).kind !== "empty");
      const stored = actor ? readRecoveryRecord(actor) : null;
      const recovery =
        this.recoveryRecord ??
        (stored?.kind === "record" ? stored.record : null);
      const blocked: WorkspaceRecoveryRecord | null = recovery
        ? {
            schemaVersion: 1,
            command: recovery.command,
            state: "blocked",
            reason: "access",
            ...("result" in recovery && recovery.result
              ? { result: recovery.result }
              : {}),
          }
        : null;
      const persisted = blockStoredRecoveriesForAccessLoss(actor);
      if (!persisted)
        this.storageError = "Не удалось записать остановку восстановления";
      if (blocked && !writeRecoveryRecord(blocked))
        this.storageError = "Не удалось записать остановку восстановления";
      if (hasRecovery || !persisted) {
        const suspended =
          accessSuspensions.get(this) ??
          new Map<string, WorkspaceRecoveryRecord | null>();
        suspended.set(
          actor ?? "*",
          blocked ?? suspended.get(actor ?? "*") ?? null,
        );
        accessSuspensions.set(this, suspended);
      }
      this.clearOpenedWorkspace({ force: true });
      if (hasRecovery || !persisted) {
        this.phase = "blocked";
        this.editBlockReason = "ACCESS_LOST";
      }
    },
    hasAccessSuspension(actorId: string): boolean {
      const suspended = accessSuspensions.get(this);
      if (!suspended?.has(actorId) && !suspended?.has("*")) return false;
      const record = suspended.get(actorId);
      if (record && !writeRecoveryRecord(record))
        this.storageError = "Не удалось записать остановку восстановления";
      this.phase = "blocked";
      this.editBlockReason = "RECOVERY_REQUIRES_CONFIRMATION";
      return true;
    },
    allowWorkspaceNavigation(): boolean {
      if (this.canLeaveWorkspace) return true;
      this.editBlockReason = "FINISH_OR_CANCEL_LOCAL_WORK";
      return false;
    },
    persistRecovery(): boolean {
      if (!this.recoveryRecord || !writeRecoveryRecord(this.recoveryRecord)) {
        this.storageError = "Не удалось сохранить контекст восстановления";
        this.editBlockReason = "RECOVERY_STORAGE_UNAVAILABLE";
        return false;
      }
      this.storageError = null;
      return true;
    },
    isCurrentCommand(command: PendingGeometryCommand, seq: number): boolean {
      const auth = useAuthStore();
      return (
        this.editRequestSeq === seq &&
        auth.isAuthenticated &&
        auth.user?.id === command.actorId &&
        this.openedWorkOrderId === command.target.workOrderId &&
        this.openedEditVersionId === command.target.editVersionId &&
        this.pendingCommand?.request.commandId === command.request.commandId
      );
    },
    async saveLocalDraft(): Promise<void> {
      const auth = useAuthStore();
      if (auth.user && this.hasAccessSuspension(auth.user.id)) return;
      if (
        this.workspaceInteractionLocked ||
        this.storageError ||
        !auth.isAuthenticated ||
        !auth.user ||
        auth.user.role !== "editor" ||
        !this.localDraft ||
        !isLocalDraftDirty(this.localDraft) ||
        !this.activeWorkspace ||
        this.recoveryRecord ||
        !["editing", "rejected"].includes(this.phase)
      )
        return;
      if (
        this.rejectedCandidateGeometry &&
        JSON.stringify(this.localDraft.candidateGeometry.coordinates) ===
          JSON.stringify(this.rejectedCandidateGeometry.coordinates)
      )
        return;
      const existing = readRecoveryRecord(auth.user.id);
      if (existing.kind !== "empty") {
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_REQUIRED";
        return;
      }
      const command: PendingGeometryCommand = {
        actorId: auth.user.id,
        target: {
          workOrderId: this.activeWorkspace.workOrder.id,
          editVersionId: this.activeWorkspace.workOrder.editVersion.id,
          featureId: this.localDraft.featureId,
        },
        request: {
          commandId: crypto.randomUUID(),
          draftVersionToken: this.localDraft.sourceToken,
          geometry: copyGeometry(this.localDraft.candidateGeometry),
        },
      };
      await submitGeometryCommand(this, command);
    },
    async sendPendingOnce(
      command: PendingGeometryCommand,
      seq: number,
      hadUnknownOutcome: boolean,
    ): Promise<boolean> {
      if (!this.isCurrentCommand(command, seq)) return false;
      this.phase = "sending";
      let result: GeometrySaveResult;
      try {
        result = parseGeometrySaveResult(
          await saveFeatureGeometry(command.target, command.request),
          command.target,
          command.request.commandId,
        );
      } catch (error) {
        if (!this.isCurrentCommand(command, seq)) return false;
        const failure = classifySaveFailure(error, hadUnknownOutcome);
        if (failure.kind === "retryableUnknown") {
          this.phase = "unknown";
          this.saveError = "Результат сохранения пока неизвестен";
          return true;
        }
        if (failure.kind === "blocked") {
          if (failure.reason === "access") {
            this.suspendWorkspaceRecoveryForAccessLoss(command.actorId);
            this.saveError = failure.code;
            return false;
          }
          this.recoveryRecord = {
            schemaVersion: 1,
            command,
            state: "blocked",
            reason: failure.reason,
          };
          this.phase = "blocked";
          this.saveError = failure.code;
          this.editBlockReason = failure.code;
          this.persistRecovery();
          return false;
        }
        this.saveError = failure.error.code;
        this.rejectedCandidateGeometry = copyGeometry(command.request.geometry);
        this.recoveryRecord = {
          schemaVersion: 1,
          command,
          state: "rejected",
          error: failure.error,
          needsReadback: failure.kind === "stale",
        };
        this.phase = failure.kind === "stale" ? "stale" : "rejected";
        if (!this.persistRecovery()) {
          this.phase = "blocked";
          return false;
        }
        if (failure.kind === "stale") await this.refreshCurrentWorkspace();
        else this.finishRecovery();
        return false;
      }
      if (!this.isCurrentCommand(command, seq)) return false;
      this.commandResult = result;
      this.recoveryRecord = {
        schemaVersion: 1,
        command,
        state: "succeeded",
        result,
      };
      this.localDraft = null;
      this.phase = "reading-current";
      if (!this.persistRecovery()) return false;
      await this.refreshCurrentWorkspace();
      return false;
    },
    finishRecovery(): boolean {
      const recovery = this.recoveryRecord;
      if (
        !recovery ||
        (recovery.state !== "succeeded" && recovery.state !== "rejected")
      )
        return false;
      if (
        !removeRecoveryRecord(
          recovery.command.actorId,
          recovery.command.request.commandId,
        )
      ) {
        this.storageError =
          "Не удалось завершить очистку контекста восстановления";
        this.editBlockReason = "RECOVERY_STORAGE_UNAVAILABLE";
        return false;
      }
      this.recoveryRecord = null;
      this.storageError = null;
      this.editBlockReason = null;
      this.phase =
        recovery.state === "succeeded"
          ? "idle"
          : recovery.error.code === "DRAFT_VERSION_STALE"
            ? "stale"
            : "rejected";
      return true;
    },
    async refreshCurrentWorkspace(): Promise<void> {
      if (
        this.recoveryReadSeq !== null ||
        this.storageError ||
        this.phase === "blocked" ||
        !this.activeWorkspace ||
        useAuthStore().user?.role !== "editor"
      )
        return;
      const recovery = this.recoveryRecord;
      if (
        !recovery ||
        (recovery.state !== "succeeded" && recovery.state !== "rejected")
      )
        return;
      const seq = this.editRequestSeq;
      if (!this.isCurrentCommand(recovery.command, seq)) return;
      if (!this.persistRecovery()) return;
      if (recovery.state === "rejected" && !recovery.needsReadback) {
        this.finishRecovery();
        return;
      }
      const readSeq = ++this.openWorkspaceRequestSeq;
      this.recoveryReadSeq = readSeq;
      this.phase = "reading-current";
      this.readbackError = null;
      try {
        const { workOrderId, editVersionId } = recovery.command.target;
        const current = parseWorkspaceResponse(
          await fetchWorkspace(workOrderId, editVersionId),
          workOrderId,
          editVersionId,
        );
        if (
          !this.isCurrentCommand(recovery.command, seq) ||
          readSeq !== this.openWorkspaceRequestSeq
        )
          return;
        this.workspace = current;
        this.finishRecovery();
      } catch (error) {
        if (
          this.isCurrentCommand(recovery.command, seq) &&
          readSeq === this.openWorkspaceRequestSeq
        ) {
          if (isWorkspaceAccessFailure(parseApiError(error))) {
            this.suspendWorkspaceRecoveryForAccessLoss(
              recovery.command.actorId,
            );
            return;
          }
          this.readbackError =
            "Актуальные данные не загружены. Повторите чтение рабочего пространства.";
        }
      } finally {
        if (this.recoveryReadSeq === readSeq) this.recoveryReadSeq = null;
      }
    },
    discardRejectedAttempt(): boolean {
      if (!this.canDiscardRejectedAttempt) return false;
      return this.cancelLocalEdit();
    },
    async retryPendingSave(): Promise<void> {
      if (
        !this.canRetryPendingCommand ||
        !this.recoveryRecord ||
        retryControllers.has(this)
      )
        return;
      if (this.hasAccessSuspension(this.recoveryRecord.command.actorId)) return;
      await this.runPendingRetries(
        this.recoveryRecord.command,
        ++this.editRequestSeq,
      );
    },
    async runPendingRetries(
      command: PendingGeometryCommand,
      seq: number,
    ): Promise<void> {
      if (retryControllers.has(this)) return;
      const controller = new AbortController();
      retryControllers.set(this, controller);
      try {
        for (const delay of AUTO_RETRY_DELAYS_MS) {
          if (!this.isCurrentCommand(command, seq)) return;
          this.phase = "retry-wait";
          if (
            !(await waitForRetry(delay, controller.signal)) ||
            !this.isCurrentCommand(command, seq)
          )
            return;
          if (!(await this.sendPendingOnce(command, seq, true))) return;
        }
      } finally {
        if (retryControllers.get(this) === controller)
          retryControllers.delete(this);
      }
    },
    async restorePendingSave(): Promise<void> {
      const auth = useAuthStore();
      if (auth.user && this.hasAccessSuspension(auth.user.id)) return;
      if (
        !auth.isAuthenticated ||
        !auth.user ||
        !this.activeWorkspace ||
        this.recoveryRecord ||
        this.localDraft ||
        this.phase === "blocked"
      )
        return;
      const stored = readRecoveryRecord(auth.user.id);
      if (stored.kind === "empty") return;
      if (stored.kind !== "record") {
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_STORAGE_INVALID";
        return;
      }
      const recovery = stored.record;
      freezePendingCommand(recovery.command);
      if (
        recovery.command.target.workOrderId !== this.openedWorkOrderId ||
        recovery.command.target.editVersionId !== this.openedEditVersionId
      ) {
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_OTHER_WORKSPACE";
        return;
      }
      this.recoveryRecord = recovery;
      const seq = ++this.editRequestSeq;
      this.openWorkspaceRequestSeq += 1;
      if (recovery.state === "blocked") {
        this.phase = "blocked";
        this.editBlockReason = "RECOVERY_REQUIRES_CONFIRMATION";
        return;
      }
      if (recovery.state === "succeeded") {
        this.commandResult = recovery.result;
        await this.refreshCurrentWorkspace();
        return;
      }
      if (recovery.state === "rejected") {
        this.saveError = recovery.error.code;
        await this.refreshCurrentWorkspace();
        return;
      }
      await this.runPendingRetries(recovery.command, seq);
    },
    beginLocalEdit(featureId: string, vertexIndex: number): boolean {
      if (
        this.workspaceInteractionLocked ||
        !this.activeWorkspace ||
        this.storageError ||
        ["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
          this.saveError ?? "",
        ) ||
        this.recoveryRecord ||
        !["idle", "editing", "rejected"].includes(this.phase)
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
          this.activeWorkspace,
          featureId,
          vertexIndex,
        );
        this.phase = "editing";
        this.editBlockReason = null;
        return true;
      } catch {
        this.editBlockReason = "INVALID_LOCAL_EDIT";
        return false;
      }
    },
    moveLocalVertex(xy: [number, number]): boolean {
      if (
        this.workspaceInteractionLocked ||
        !this.localDraft ||
        this.storageError ||
        ["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
          this.saveError ?? "",
        ) ||
        this.recoveryRecord ||
        !["editing", "rejected"].includes(this.phase)
      )
        return false;
      try {
        this.localDraft = updateLocalVertex(this.localDraft, xy);
        this.phase = "editing";
        return true;
      } catch {
        this.editBlockReason = "INVALID_LOCAL_EDIT";
        return false;
      }
    },
    cancelLocalEdit(): boolean {
      if (
        this.workspaceInteractionLocked ||
        this.storageError ||
        this.readbackError ||
        this.recoveryRecord ||
        !["idle", "editing", "rejected", "stale"].includes(this.phase)
      )
        return false;
      this.localDraft = null;
      this.rejectedCandidateGeometry = null;
      this.saveError = null;
      this.phase = "idle";
      this.editBlockReason = null;
      return true;
    },
    discardLocalChangesKeepingSelection(): boolean {
      const auth = useAuthStore();
      if (
        this.workspaceInteractionLocked ||
        !auth.isAuthenticated ||
        auth.user?.role !== "editor" ||
        this.hasAccessSuspension(auth.user.id) ||
        !this.activeWorkspace ||
        !this.localDraft ||
        !isLocalDraftDirty(this.localDraft) ||
        this.recoveryRecord ||
        this.storageError ||
        !["editing", "rejected"].includes(this.phase)
      )
        return false;
      const draft = createLocalDraft(
        this.activeWorkspace,
        this.localDraft.featureId,
        this.localDraft.vertexIndex,
      );
      this.localDraft = draft;
      this.phase = "editing";
      this.saveError = null;
      this.editBlockReason = null;
      this.commandResult = null;
      this.submittedSourceGeometry = null;
      this.submittedCommandId = null;
      this.rejectedCandidateGeometry = null;
      return true;
    },
    reset(options: ResetWorkOrdersOptions = {}): void {
      if (this.revertConfirmation)
        this.cancelRevert(this.revertConfirmation.confirmationId);
      if (this.recoveryRecord) this.suspendWorkspaceRecoveryForAccessLoss();
      retryControllers.get(this)?.abort();
      retryControllers.delete(this);
      const nextEditRequestSeq = this.editRequestSeq + 1;
      const nextLoadAssignedRequestSeq = this.loadAssignedRequestSeq + 1;
      const nextOpenWorkspaceRequestSeq = this.openWorkspaceRequestSeq + 1;

      Object.assign(this, {
        ...createInitialWorkOrdersState(),
        editRequestSeq: nextEditRequestSeq,
        loadAssignedRequestSeq: nextLoadAssignedRequestSeq,
        openWorkspaceRequestSeq: nextOpenWorkspaceRequestSeq,
      });
      if (!options.preserveSelectedWorkOrder) {
        clearStoredSelectedWorkOrder();
      }
      if (!options.preserveOpenedWorkspace) {
        clearStoredOpenedWorkspace();
      }
    },
    async loadAssigned() {
      const requestSeq = this.loadAssignedRequestSeq + 1;
      this.loadAssignedRequestSeq = requestSeq;
      this.isLoading = true;
      this.loadError = null;
      try {
        const result = await fetchAssignedWorkOrders();
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

        this.items = result.workOrders;
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        ) {
          this.suspendWorkspaceRecoveryForAccessLoss();
          this.clearSelection(true);
        }
        if (
          this.openedWorkOrderId &&
          !this.items.some((item) => item.id === this.openedWorkOrderId)
        ) {
          this.suspendWorkspaceRecoveryForAccessLoss();
          this.clearOpenedWorkspace({ force: true });
        }
      } catch (error: unknown) {
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

        this.items = [];
        const parsed = parseApiError(error);
        if (isWorkspaceAccessFailure(parsed))
          this.suspendWorkspaceRecoveryForAccessLoss();
        this.loadError = presentWorkOrdersLoadError(parsed);
      } finally {
        if (this.loadAssignedRequestSeq === requestSeq) {
          this.isLoading = false;
        }
      }
    },
    selectWorkOrder(workOrderId: string): void {
      if (this.selectedWorkOrderId === workOrderId) {
        storeSelectedWorkOrder(workOrderId);
        return;
      }

      if (!this.allowWorkspaceNavigation()) return;

      this.openWorkspaceRequestSeq += 1;
      this.clearOpenedWorkspace();
      this.selectedWorkOrderId = workOrderId;
      storeSelectedWorkOrder(workOrderId);
    },
    clearSelection(force = false): void {
      if (!force && !this.allowWorkspaceNavigation()) return;
      this.openWorkspaceRequestSeq += 1;
      this.selectedWorkOrderId = null;
      clearStoredSelectedWorkOrder();
      this.clearOpenedWorkspace({ force });
    },
    async openSelectedWorkOrder() {
      if (!this.allowWorkspaceNavigation()) return;
      const workOrderId = this.selectedWorkOrderId;
      if (!workOrderId || this.openingWorkOrderId !== null) {
        return;
      }

      const requestSeq = this.openWorkspaceRequestSeq + 1;
      this.openWorkspaceRequestSeq = requestSeq;
      this.openingWorkOrderId = workOrderId;
      this.openingWorkspaceRequestSeq = requestSeq;
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
        [workOrderId]: undefined,
      };
      this.openWorkspaceErrorOperationByWorkOrderId = {
        ...this.openWorkspaceErrorOperationByWorkOrderId,
        [workOrderId]: undefined,
      };

      try {
        const openResult = await openEditVersion(workOrderId);
        if (
          this.openWorkspaceRequestSeq !== requestSeq ||
          this.selectedWorkOrderId !== workOrderId
        ) {
          return;
        }

        this.updateWorkOrderStatus(workOrderId, "in_progress");

        const editVersionId = openResult.editVersion.id;
        const workspace = await fetchWorkspace(workOrderId, editVersionId);

        if (
          this.openWorkspaceRequestSeq !== requestSeq ||
          this.selectedWorkOrderId !== workOrderId
        ) {
          return;
        }

        this.openedWorkOrderId = workOrderId;
        this.openedEditVersionId = editVersionId;
        this.workspace = workspace;
        storeOpenedWorkspace({ workOrderId, editVersionId });
        this.openWorkspaceErrorByWorkOrderId = {
          ...this.openWorkspaceErrorByWorkOrderId,
          [workOrderId]: undefined,
        };
        this.openWorkspaceErrorOperationByWorkOrderId = {
          ...this.openWorkspaceErrorOperationByWorkOrderId,
          [workOrderId]: undefined,
        };
        await this.restorePendingSave();
      } catch (error: unknown) {
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          const parsed = parseApiError(error);
          if (isWorkspaceAccessFailure(parsed))
            this.suspendWorkspaceRecoveryForAccessLoss();
          const errorPresentation = presentWorkspaceOpenError(parsed);
          this.openWorkspaceErrorByWorkOrderId = {
            ...this.openWorkspaceErrorByWorkOrderId,
            [workOrderId]: errorPresentation ?? undefined,
          };
          this.openWorkspaceErrorOperationByWorkOrderId = {
            ...this.openWorkspaceErrorOperationByWorkOrderId,
            [workOrderId]: errorPresentation ? "open" : undefined,
          };
        }
      } finally {
        if (this.openingWorkspaceRequestSeq === requestSeq) {
          this.openingWorkOrderId = null;
          this.openingWorkspaceRequestSeq = null;
        }
      }
    },
    async restoreOpenedWorkspace() {
      if (!this.allowWorkspaceNavigation()) return;
      if (this.openingWorkOrderId !== null) {
        return;
      }

      const storedSelection = readStoredSelectedWorkOrder();
      const storedWorkspace = readStoredOpenedWorkspace();
      const workOrderId =
        this.selectedWorkOrderId ??
        storedSelection?.workOrderId ??
        storedWorkspace?.workOrderId ??
        null;

      if (!workOrderId) {
        return;
      }

      if (!this.items.some((item) => item.id === workOrderId)) {
        this.suspendWorkspaceRecoveryForAccessLoss();
        this.selectedWorkOrderId = null;
        clearStoredSelectedWorkOrder();
        this.clearOpenedWorkspace({ force: true });
        return;
      }

      this.selectedWorkOrderId = workOrderId;
      storeSelectedWorkOrder(workOrderId);

      if (!storedWorkspace) {
        return;
      }

      if (storedWorkspace.workOrderId !== workOrderId) {
        this.clearOpenedWorkspace();
        return;
      }

      if (this.isWorkOrderOpened(workOrderId)) {
        return;
      }

      const editVersionId = storedWorkspace.editVersionId;
      const requestSeq = this.openWorkspaceRequestSeq + 1;
      this.openWorkspaceRequestSeq = requestSeq;
      this.openingWorkOrderId = workOrderId;
      this.openingWorkspaceRequestSeq = requestSeq;
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
        [workOrderId]: undefined,
      };
      this.openWorkspaceErrorOperationByWorkOrderId = {
        ...this.openWorkspaceErrorOperationByWorkOrderId,
        [workOrderId]: undefined,
      };

      try {
        const workspace = await fetchWorkspace(workOrderId, editVersionId);
        if (
          this.openWorkspaceRequestSeq !== requestSeq ||
          this.selectedWorkOrderId !== workOrderId
        ) {
          return;
        }

        this.updateWorkOrderStatus(workOrderId, workspace.workOrder.status);
        this.openedWorkOrderId = workOrderId;
        this.openedEditVersionId = editVersionId;
        this.workspace = workspace;
        storeOpenedWorkspace({ workOrderId, editVersionId });
        this.openWorkspaceErrorByWorkOrderId = {
          ...this.openWorkspaceErrorByWorkOrderId,
          [workOrderId]: undefined,
        };
        this.openWorkspaceErrorOperationByWorkOrderId = {
          ...this.openWorkspaceErrorOperationByWorkOrderId,
          [workOrderId]: undefined,
        };
        await this.restorePendingSave();
      } catch (error: unknown) {
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          const parsed = parseApiError(error);
          if (isWorkspaceAccessFailure(parsed))
            this.suspendWorkspaceRecoveryForAccessLoss();
          const errorPresentation = presentWorkspaceRestoreError(parsed);
          this.clearOpenedWorkspace({
            force: isWorkspaceAccessFailure(parsed),
            preserveStoredWorkspace: shouldPreserveStoredWorkspace(parsed),
          });
          this.openWorkspaceErrorByWorkOrderId = {
            ...this.openWorkspaceErrorByWorkOrderId,
            [workOrderId]: errorPresentation ?? undefined,
          };
          this.openWorkspaceErrorOperationByWorkOrderId = {
            ...this.openWorkspaceErrorOperationByWorkOrderId,
            [workOrderId]: errorPresentation ? "restore" : undefined,
          };
        }
      } finally {
        if (this.openingWorkspaceRequestSeq === requestSeq) {
          this.openingWorkOrderId = null;
          this.openingWorkspaceRequestSeq = null;
        }
      }
    },
    isWorkOrderOpened(workOrderId: string): boolean {
      return (
        this.openedWorkOrderId === workOrderId &&
        this.workspace !== null &&
        this.openedEditVersionId !== null
      );
    },
    markWorkspaceFitted(workspaceKey: string): void {
      this.lastFittedWorkspaceKey = workspaceKey;
    },
    shouldFitWorkspace(workspaceKey: string | null): boolean {
      return (
        workspaceKey !== null && this.lastFittedWorkspaceKey !== workspaceKey
      );
    },
    async retrySelectedWorkspaceError(): Promise<void> {
      if (this.selectedOpenWorkspaceErrorOperation === "restore") {
        await this.restoreOpenedWorkspace();
        return;
      }
      await this.openSelectedWorkOrder();
    },
    async reopenSelectedWorkOrder(): Promise<void> {
      if (!this.allowWorkspaceNavigation()) return;
      clearStoredOpenedWorkspace();
      await this.openSelectedWorkOrder();
    },
    updateWorkOrderStatus(workOrderId: string, status: WorkOrderStatus): void {
      this.items = this.items.map((item) =>
        item.id === workOrderId ? { ...item, status } : item,
      );
    },
    clearOpenedWorkspace(options: ClearOpenedWorkspaceOptions = {}): void {
      if (!options.force && !this.allowWorkspaceNavigation()) return;
      this.submittedSourceGeometry = null;
      this.submittedCommandId = null;
      this.rejectedCandidateGeometry = null;
      this.localDraft = null;
      if (options.force) {
        this.recoveryRecord = null;
        this.commandResult = null;
      }
      this.openedWorkOrderId = null;
      this.openedEditVersionId = null;
      this.workspace = null;
      this.lastFittedWorkspaceKey = null;
      if (!options.preserveStoredWorkspace) {
        clearStoredOpenedWorkspace();
      }
    },
  },
});

async function submitGeometryCommand(
  store: ReturnType<typeof useWorkOrdersStore>,
  command: PendingGeometryCommand,
): Promise<void> {
  freezePendingCommand(command);
  store.recoveryRecord = { schemaVersion: 1, command, state: "unknown" };
  if (!store.persistRecovery()) {
    store.recoveryRecord = null;
    return;
  }
  const source =
    store.activeWorkspace!.workOrder.editVersion.features.features.find(
      (feature) => feature.id === command.target.featureId,
    )?.geometry;
  store.submittedSourceGeometry = isLineStringXY(source)
    ? copyGeometry(source)
    : null;
  store.submittedCommandId = command.request.commandId;
  store.rejectedCandidateGeometry = null;
  store.commandResult = null;
  store.saveError = null;
  store.readbackError = null;
  store.openWorkspaceRequestSeq += 1;
  const seq = ++store.editRequestSeq;
  if (await store.sendPendingOnce(command, seq, false))
    await store.runPendingRetries(command, seq);
}
