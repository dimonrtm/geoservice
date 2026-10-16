import { defineStore } from "pinia";
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

type WorkOrdersState = {
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
    pendingCommand: (state): PendingGeometryCommand | null =>
      state.recoveryRecord?.command ?? null,
    canLeaveWorkspace: (state): boolean =>
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
        !auth.isAuthenticated ||
        !auth.user ||
        !this.localDraft ||
        !isLocalDraftDirty(this.localDraft) ||
        !this.activeWorkspace ||
        this.recoveryRecord ||
        !["editing", "rejected"].includes(this.phase)
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
      freezePendingCommand(command);
      this.recoveryRecord = { schemaVersion: 1, command, state: "unknown" };
      if (!this.persistRecovery()) {
        this.recoveryRecord = null;
        return;
      }
      this.commandResult = null;
      this.saveError = null;
      this.readbackError = null;
      this.openWorkspaceRequestSeq += 1;
      const seq = ++this.editRequestSeq;
      if (await this.sendPendingOnce(command, seq, false))
        await this.runPendingRetries(command, seq);
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
      }
    },
    async retryPendingSave(): Promise<void> {
      if (this.phase !== "unknown" || this.recoveryRecord?.state !== "unknown")
        return;
      await this.sendPendingOnce(
        this.recoveryRecord.command,
        ++this.editRequestSeq,
        true,
      );
    },
    async runPendingRetries(
      command: PendingGeometryCommand,
      seq: number,
    ): Promise<void> {
      retryControllers.get(this)?.abort();
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
        !this.activeWorkspace ||
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
        !this.localDraft ||
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
        this.recoveryRecord ||
        !["idle", "editing", "rejected", "stale"].includes(this.phase)
      )
        return false;
      this.localDraft = null;
      this.phase = "idle";
      this.editBlockReason = null;
      return true;
    },
    reset(options: ResetWorkOrdersOptions = {}): void {
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
