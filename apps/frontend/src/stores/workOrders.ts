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
  type GeometrySaveResult,
  type WorkspaceRecoveryRecord,
  type PendingGeometryCommand,
  type LineStringXY,
  isLineStringXY,
} from "@/contracts/workspace-edit";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import {
  recoveryKey,
  type RecoveryContext,
  type ReadTicket,
  type RecoveryApplyResult,
  type RecoveryCompletion,
  type RecoverySource,
} from "@/contracts/workspace-recovery";
import type {
  NavigationTarget,
  NavigationChoice,
  NavigationContext,
} from "@/domain/workspaceNavigation";
const confirmationWatchers = new WeakMap<object, WatchStopHandle>();
const recoveryBindings = new WeakMap<object, () => void>();

import {
  fetchAssignedWorkOrders,
  fetchWorkspace,
  openEditVersion,
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
  comparisonPreview: "source" | "candidate" | "current" | null;
  navigation: NavigationContext | null;
  navigationError: string | null;
  snapshots: Record<string, WorkspaceResponse>;
  readGenerations: Record<string, number>;
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
  editRequestSeq: number;
  saveError: string | null;
  localDraft: WorkspaceLocalDraft | null;
  commandResult: GeometrySaveResult | null;
  localPhase:
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
  openingEditVersionId: string | null;
  workspaceReadIntent: { key: string; openSeq: number } | null;
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
    comparisonPreview: null,
    navigation: null,
    navigationError: null,
    snapshots: {},
    readGenerations: {},
    staleComparisons: {},
    revertConfirmation: null,
    recoveryReadSeq: null,
    submittedSourceGeometry: null,
    submittedCommandId: null,
    rejectedCandidateGeometry: null,
    editRequestSeq: 0,
    saveError: null,
    localDraft: null,
    commandResult: null,
    localPhase: "idle",
    editBlockReason: null,
    items: [],
    isLoading: false,
    loadError: null,
    selectedWorkOrderId: null,
    openedWorkOrderId: null,
    openedEditVersionId: null,
    workspace: null,
    openingWorkOrderId: null,
    openingEditVersionId: null,
    workspaceReadIntent: null,
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
    recoveryKey(state): string | null {
      const actor = useAuthStore().user?.id;
      return actor && state.openedWorkOrderId && state.openedEditVersionId
        ? recoveryKey({
            actorId: actor,
            workOrderId: state.openedWorkOrderId,
            editVersionId: state.openedEditVersionId,
          })
        : null;
    },
    activeComparison(): WorkOrdersState["staleComparisons"][string] | null {
      const key = this.recoveryKey;
      return key ? (this.staleComparisons[key] ?? null) : null;
    },
    previewGeometry(): LineStringXY | null {
      const material = this.activeComparison;
      if (!material || !this.comparisonPreview) return null;
      if (this.comparisonPreview === "source")
        return material.source?.geometry ?? null;
      if (this.comparisonPreview === "candidate") return material.candidate;
      const geometry =
        this.activeWorkspace?.workOrder.editVersion.features.features.find(
          (f) => f.id === material.featureId,
        )?.geometry;
      return isLineStringXY(geometry) ? geometry : null;
    },
    recoveryRecord(): WorkspaceRecoveryRecord | null {
      const recoveryRecord = this.recoveryKey
        ? useWorkspaceRecoveryStore().getRecord(this.recoveryKey)
        : null;
      if (!recoveryRecord) return null;
      if (recoveryRecord.blocks.length)
        return {
          schemaVersion: 1,
          command: recoveryRecord.command,
          state: "blocked",
          reason: recoveryRecord.blocks.includes("access")
            ? "access"
            : "protocol",
          ...(recoveryRecord.outcome.kind === "succeeded"
            ? { result: recoveryRecord.outcome.result }
            : {}),
        };
      if (recoveryRecord.outcome.kind === "succeeded")
        return {
          schemaVersion: 1,
          command: recoveryRecord.command,
          state: "succeeded",
          result: recoveryRecord.outcome.result,
        };
      if (recoveryRecord.outcome.kind === "rejected")
        return {
          schemaVersion: 1,
          command: recoveryRecord.command,
          state: "rejected",
          error: recoveryRecord.outcome.error,
          needsReadback: recoveryRecord.readbackRequired,
        };
      return {
        schemaVersion: 1,
        command: recoveryRecord.command,
        state: "unknown",
      };
    },
    phase(): WorkOrdersState["localPhase"] {
      return (
        (this.recoveryKey
          ? useWorkspaceRecoveryStore().phases[this.recoveryKey]
          : null) ?? this.localPhase
      );
    },
    readbackError(): string | null {
      return (
        (this.recoveryKey
          ? useWorkspaceRecoveryStore().readbackErrors[this.recoveryKey]
          : null) ?? null
      );
    },
    storageError(): string | null {
      const r = useWorkspaceRecoveryStore();
      return (
        r.storageError ??
        (this.recoveryKey ? r.contextErrors[this.recoveryKey] : null) ??
        null
      );
    },
    workspaceInteractionLocked: (state): boolean =>
      state.revertConfirmation !== null ||
      (state.navigation !== null && state.navigation.phase !== "saving"),
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
        this.localPhase === "stale" &&
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
    pendingCommand(): PendingGeometryCommand | null {
      return this.recoveryRecord?.command ?? null;
    },
    canLeaveWorkspace(): boolean {
      return (
        !this.revertConfirmation &&
        (!this.localDraft ||
          !isLocalDraftDirty(this.localDraft) ||
          !!this.recoveryRecord ||
          this.phase === "stale")
      );
    },
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
    requestNavigation(target: NavigationTarget): string | null {
      const auth = useAuthStore();
      if (
        !auth.user ||
        this.revertConfirmation ||
        this.navigation ||
        (target.kind === "work-order" &&
          target.workOrderId === this.selectedWorkOrderId)
      )
        return null;
      const recovery = useWorkspaceRecoveryStore();
      const sent =
        target.kind === "logout"
          ? Object.values(recovery.records).some(
              (r) => r.command.actorId === auth.user!.id,
            )
          : !!this.recoveryRecord;
      const stale =
        target.kind === "logout"
          ? Object.keys(this.staleComparisons).length > 0
          : !!(this.recoveryKey && this.staleComparisons[this.recoveryKey]);
      const dirty =
        !!this.localDraft &&
        isLocalDraftDirty(this.localDraft) &&
        !this.recoveryRecord &&
        !this.activeComparison;
      if (!dirty && !sent && !stale) {
        void this.performNavigation(target);
        return null;
      }
      const id = crypto.randomUUID();
      this.navigation = {
        id,
        actorId: auth.user.id,
        sessionEpoch: auth.sessionEpoch,
        sourceKey: this.recoveryKey,
        target,
        phase: dirty ? "dirty" : sent ? "sent" : "stale",
        commandId: null,
      };
      this.navigationError = null;
      return id;
    },
    cancelNavigation(id: string): void {
      if (this.navigation?.id === id) this.navigation = null;
    },
    async prepareLogout(): Promise<boolean> {
      const actor = useAuthStore().user?.id;
      if (!actor) return true;
      const recovery = useWorkspaceRecoveryStore();
      await recovery.suspendActor(actor);
      if (recovery.storageError) {
        this.navigationError =
          "Выход приостановлен: не удалось сохранить данные восстановления. Повторите попытку.";
        return false;
      }
      return true;
    },
    async performNavigation(target: NavigationTarget): Promise<void> {
      if (target.kind === "logout") {
        if (await this.prepareLogout()) await useAuthStore().logout();
        return;
      }
      this.clearOpenedWorkspace({ force: true });
      this.selectedWorkOrderId = target.workOrderId;
      storeSelectedWorkOrder(target.workOrderId);
      this.openWorkspaceRequestSeq++;
    },
    async resolveNavigation(
      id: string,
      choice: NavigationChoice,
    ): Promise<void> {
      const context = this.navigation,
        auth = useAuthStore();
      if (!context || context.id !== id || context.phase === "saving") return;
      if (
        context.actorId !== auth.user?.id ||
        context.sessionEpoch !== auth.sessionEpoch ||
        context.sourceKey !== this.recoveryKey
      ) {
        this.navigation = null;
        return;
      }
      if (choice === "stay") {
        this.navigation = null;
        return;
      }
      if (choice === "save" && context.phase === "dirty") {
        context.phase = "saving";
        await this.saveLocalDraft();
        if (this.navigation?.id === id && !this.navigation.commandId)
          this.navigation = null;
        return;
      }
      if (
        (choice === "discard" && context.phase === "dirty") ||
        (choice === "leave" && context.phase !== "dirty")
      ) {
        this.navigation = null;
        if (choice === "discard") this.cancelLocalEdit();
        await this.performNavigation(context.target);
      }
    },
    beginRevert(): "resolve-dirty" | "confirm" | "blocked" {
      const auth = useAuthStore();
      if (
        !this.canStartRevert ||
        this.revertConfirmation ||
        !auth.user ||
        this.hasAccessSuspension(auth.user.id)
      )
        return "blocked";
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
      this.localPhase = "idle";
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
    attachRecoveryHost(): () => void {
      if (recoveryBindings.has(this)) return recoveryBindings.get(this)!;
      const recovery = useWorkspaceRecoveryStore();
      const detach = recovery.bindHost({
        session: () => {
          const auth = useAuthStore();
          return auth.isAuthenticated && auth.user
            ? {
                actorId: auth.user.id,
                epoch: auth.sessionEpoch,
                canEdit: auth.user.role === "editor",
              }
            : null;
        },
        canAccess: (context) =>
          useAuthStore().user?.id === context.actorId &&
          this.items.some((item) => item.id === context.workOrderId),
        reserveRead: (context) => this.reserveWorkspaceRead(context),
        applyRead: (ticket, workspace) =>
          this.applyWorkspaceRead(ticket, workspace),
        complete: (completion) => this.completeRecovery(completion),
        interrupted: (key, reason) => {
          if (reason === "session") {
            useAuthStore().clearLocalSession();
            return;
          }
          if (this.navigation?.sourceKey === key) this.navigation = null;
          if (reason === "access" && this.recoveryKey === key)
            this.clearOpenedWorkspace({ force: true });
        },
      });
      recoveryBindings.set(this, detach);
      return detach;
    },
    reserveWorkspaceRead(context: RecoveryContext): ReadTicket {
      const key = recoveryKey(context);
      const generation = (this.readGenerations[key] ?? 0) + 1;
      this.readGenerations[key] = generation;
      return { key, generation, sessionEpoch: useAuthStore().sessionEpoch };
    },
    applyWorkspaceRead(
      ticket: ReadTicket,
      workspace: WorkspaceResponse,
    ): RecoveryApplyResult {
      const auth = useAuthStore();
      if (
        !auth.isAuthenticated ||
        !auth.user ||
        auth.sessionEpoch !== ticket.sessionEpoch ||
        ticket.key !==
          recoveryKey({
            actorId: auth.user.id,
            workOrderId: workspace.workOrder.id,
            editVersionId: workspace.workOrder.editVersion.id,
          })
      )
        return "blocked";
      if (this.readGenerations[ticket.key] !== ticket.generation)
        return "superseded";
      this.snapshots[ticket.key] = workspace;
      if (
        this.workspaceReadIntent?.key === ticket.key &&
        this.workspaceReadIntent.openSeq === this.openWorkspaceRequestSeq &&
        this.selectedWorkOrderId === workspace.workOrder.id
      ) {
        this.openedWorkOrderId = workspace.workOrder.id;
        this.openedEditVersionId = workspace.workOrder.editVersion.id;
        storeOpenedWorkspace({
          workOrderId: this.openedWorkOrderId,
          editVersionId: this.openedEditVersionId,
        });
      }
      if (
        this.openedWorkOrderId === workspace.workOrder.id &&
        this.openedEditVersionId === workspace.workOrder.editVersion.id
      )
        this.workspace = workspace;
      return "applied";
    },
    completeRecovery({ record, sessionEpoch }: RecoveryCompletion): void {
      const auth = useAuthStore();
      if (
        auth.user?.id !== record.command.actorId ||
        auth.sessionEpoch !== sessionEpoch
      )
        return;
      const selected = this.recoveryKey === record.key;
      if (record.outcome.kind === "rejected") {
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
      } else if (record.outcome.kind === "succeeded" && selected) {
        this.commandResult = record.outcome.result;
        this.submittedSourceGeometry = record.source?.geometry ?? null;
        this.submittedCommandId = record.command.request.commandId;
        this.localDraft = null;
        this.rejectedCandidateGeometry = null;
        this.saveError = null;
        this.localPhase = "idle";
        const navigation = this.navigation;
        if (
          navigation?.sourceKey === record.key &&
          navigation.commandId === record.command.request.commandId &&
          navigation.sessionEpoch === sessionEpoch
        ) {
          this.navigation = null;
          void this.performNavigation(navigation.target);
        }
      }
    },
    suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void {
      const actor = actorId ?? useAuthStore().user?.id;
      if (actor) void useWorkspaceRecoveryStore().suspendActor(actor);
      this.navigation = null;
      this.clearOpenedWorkspace({ force: true });
    },
    async suspendWorkOrderRecovery(workOrderId: string): Promise<void> {
      const auth = useAuthStore(),
        recovery = useWorkspaceRecoveryStore();
      const actor = auth.user?.id;
      if (this.openedWorkOrderId === workOrderId)
        this.clearOpenedWorkspace({ force: true });
      if (actor) await recovery.suspendActor(actor, workOrderId);
    },
    hasAccessSuspension(actorId: string): boolean {
      return (
        this.recoveryRecord?.command.actorId === actorId &&
        this.recoveryRecord.state === "blocked"
      );
    },
    allowWorkspaceNavigation(): boolean {
      if (this.canLeaveWorkspace) return true;
      this.editBlockReason = "FINISH_OR_CANCEL_LOCAL_WORK";
      return false;
    },
    async saveLocalDraft(): Promise<void> {
      const auth = useAuthStore();
      if (
        this.workspaceInteractionLocked ||
        this.storageError ||
        !auth.isAuthenticated ||
        auth.user?.role !== "editor" ||
        !this.localDraft ||
        !isLocalDraftDirty(this.localDraft) ||
        !this.activeWorkspace ||
        this.recoveryRecord ||
        !["editing", "rejected"].includes(this.phase)
      )
        return;
      if (
        this.rejectedCandidateGeometry &&
        JSON.stringify(this.rejectedCandidateGeometry.coordinates) ===
          JSON.stringify(this.localDraft.candidateGeometry.coordinates)
      )
        return;
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
      if (this.navigation?.phase === "saving")
        this.navigation.commandId = command.request.commandId;
      await submitGeometryCommand(this, command);
    },
    async refreshCurrentWorkspace(): Promise<void> {
      if (this.canRetryCurrentRead && this.recoveryKey)
        await useWorkspaceRecoveryStore().retryRead(this.recoveryKey);
    },
    async retryPendingSave(): Promise<void> {
      if (this.recoveryKey)
        await useWorkspaceRecoveryStore().retry(this.recoveryKey);
    },
    async restorePendingSave(): Promise<void> {
      this.attachRecoveryHost();
      const auth = useAuthStore();
      if (auth.user)
        await useWorkspaceRecoveryStore().initializeActor(auth.user.id);
      if (this.recoveryKey && this.staleComparisons[this.recoveryKey]) {
        this.localPhase = "stale";
        this.saveError = "DRAFT_VERSION_STALE";
      }
    },
    discardRejectedAttempt(): boolean {
      if (!this.canDiscardRejectedAttempt) return false;
      this.comparisonPreview = null;
      if (this.recoveryKey) delete this.staleComparisons[this.recoveryKey];
      return this.cancelLocalEdit();
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
        this.localPhase = "editing";
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
        this.localPhase = "editing";
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
      if (this.recoveryKey) delete this.staleComparisons[this.recoveryKey];
      this.comparisonPreview = null;
      this.localDraft = null;
      this.rejectedCandidateGeometry = null;
      this.saveError = null;
      this.localPhase = "idle";
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
      this.localPhase = "editing";
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
        const recovery = useWorkspaceRecoveryStore();
        for (const record of Object.values(recovery.records)) {
          if (
            record.command.actorId === useAuthStore().user?.id &&
            !this.items.some(
              (item) => item.id === record.command.target.workOrderId,
            )
          )
            void recovery.suspend(record.key);
        }
        this.attachRecoveryHost();
        const actor = useAuthStore().user;
        if (actor?.role === "editor") await recovery.initializeActor(actor.id);
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        ) {
          this.clearSelection(true);
        }
        if (
          this.openedWorkOrderId &&
          !this.items.some((item) => item.id === this.openedWorkOrderId)
        ) {
          this.clearOpenedWorkspace({ force: true });
        }
      } catch (error: unknown) {
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

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

      if (
        !this.canLeaveWorkspace ||
        this.recoveryRecord ||
        (this.recoveryKey && this.staleComparisons[this.recoveryKey])
      ) {
        this.requestNavigation({ kind: "work-order", workOrderId });
        return;
      }

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

      let readTicket: ReadTicket | null = null;
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
        this.openingEditVersionId = editVersionId;
        const actorId = useAuthStore().user?.id;
        if (!actorId) return;
        const ticket = this.reserveWorkspaceRead({
          actorId,
          workOrderId,
          editVersionId,
        });
        readTicket = ticket;
        this.workspaceReadIntent = { key: ticket.key, openSeq: requestSeq };
        const workspace = await fetchWorkspace(workOrderId, editVersionId);
        if (this.applyWorkspaceRead(ticket, workspace) !== "applied") return;

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
          readTicket &&
          (this.readGenerations[readTicket.key] !== readTicket.generation ||
            useAuthStore().sessionEpoch !== readTicket.sessionEpoch)
        )
          return;
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          const parsed = parseApiError(error);
          if (isWorkspaceAccessFailure(parsed))
            await this.suspendWorkOrderRecovery(workOrderId);
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
          this.openingEditVersionId = null;
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
        await this.suspendWorkOrderRecovery(workOrderId);
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
      this.openingEditVersionId = editVersionId;
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

      let readTicket: ReadTicket | null = null;
      try {
        const actorId = useAuthStore().user?.id;
        if (!actorId) return;
        const ticket = this.reserveWorkspaceRead({
          actorId,
          workOrderId,
          editVersionId,
        });
        readTicket = ticket;
        this.workspaceReadIntent = { key: ticket.key, openSeq: requestSeq };
        const workspace = await fetchWorkspace(workOrderId, editVersionId);
        if (this.applyWorkspaceRead(ticket, workspace) !== "applied") return;
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
          readTicket &&
          (this.readGenerations[readTicket.key] !== readTicket.generation ||
            useAuthStore().sessionEpoch !== readTicket.sessionEpoch)
        )
          return;
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          const parsed = parseApiError(error);
          if (isWorkspaceAccessFailure(parsed))
            await this.suspendWorkOrderRecovery(workOrderId);
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
          this.openingEditVersionId = null;
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
      this.workspaceReadIntent = null;
      this.comparisonPreview = null;
      this.submittedSourceGeometry = null;
      this.submittedCommandId = null;
      this.rejectedCandidateGeometry = null;
      this.localDraft = null;
      this.localPhase = "idle";
      this.saveError = null;
      if (options.force) {
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
  const workspace = store.activeWorkspace;
  const submitEpoch = useAuthStore().sessionEpoch;
  if (!workspace) return;
  const geometry = workspace.workOrder.editVersion.features.features.find(
    (f) => f.id === command.target.featureId,
  )?.geometry;
  if (!isLineStringXY(geometry)) return;
  const vertexIndex =
    store.localDraft?.vertexIndex ??
    workspace.workOrder.editVersion.changeSet?.vertexIndex;
  if (vertexIndex === undefined) return;
  const source = { geometry: copyGeometry(geometry), vertexIndex };
  store.localPhase = "sending";
  store.attachRecoveryHost();
  const recovery = useWorkspaceRecoveryStore();
  await recovery.initializeActor(command.actorId);
  if (
    useAuthStore().sessionEpoch !== submitEpoch ||
    useAuthStore().user?.id !== command.actorId ||
    store.openedWorkOrderId !== command.target.workOrderId ||
    store.openedEditVersionId !== command.target.editVersionId
  )
    return;
  store.submittedSourceGeometry = source.geometry;
  store.submittedCommandId = command.request.commandId;
  store.commandResult = null;
  store.saveError = null;
  store.rejectedCandidateGeometry = null;
  const started = await recovery.submit(command, source);
  if (
    started === "blocked" &&
    useAuthStore().user?.id === command.actorId &&
    store.openedEditVersionId === command.target.editVersionId
  ) {
    store.localPhase = store.storageError ? "blocked" : "editing";
    store.navigation = null;
  }
}
