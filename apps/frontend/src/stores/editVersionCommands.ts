import { defineStore } from "pinia";
import { watch, type WatchStopHandle } from "vue";
import { isLocalDraftDirty } from "@/domain/workspaceDraft";
import {
  copyGeometry,
  type GeometrySaveResult,
  type WorkspaceRecoveryRecord,
  type PendingGeometryCommand,
  type LineStringXY,
  type SaveTarget,
  isLineStringXY,
} from "@/contracts/workspace-edit";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import {
  recoveryKey,
  type RecoveryCompletion,
  type RecoverySource,
} from "@/contracts/workspace-recovery";
const confirmationWatchers = new WeakMap<object, WatchStopHandle>();
const recoveryBindings = new WeakMap<object, () => void>();

import { useEditVersionEditor } from "@/composables/useEditVersionEditor";
import { useEditVersionDraftStore } from "@/stores/editVersionDraft";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useEditorNavigationStore } from "@/stores/editorNavigation";
import { useEditorSessionStore } from "@/stores/editorSession";
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
};

export const useEditVersionCommandsStore = defineStore("editVersionCommands", {
  state: (): EditVersionCommandsState => ({
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
      const { auth, editorSession } = useCommandStores();
      const actor = auth.user?.id;
      return actor &&
        editorSession.openedWorkOrderId &&
        editorSession.openedEditVersionId
        ? recoveryKey({
            actorId: actor,
            workOrderId: editorSession.openedWorkOrderId,
            editVersionId: editorSession.openedEditVersionId,
          })
        : null;
    },
    activeComparison():
      | EditVersionCommandsState["staleComparisons"][string]
      | null {
      const key = this.recoveryKey;
      return key ? (this.staleComparisons[key] ?? null) : null;
    },
    previewGeometry(): LineStringXY | null {
      const { editorSession } = useCommandStores();
      const material = this.activeComparison;
      if (!material || !this.comparisonPreview) return null;
      if (this.comparisonPreview === "source")
        return material.source?.geometry ?? null;
      if (this.comparisonPreview === "candidate") return material.candidate;
      return findFeatureLineGeometry(
        editorSession.activeWorkspace,
        material.featureId,
      );
    },
    recoveryRecord(): WorkspaceRecoveryRecord | null {
      const { recovery } = useCommandStores();
      const recoveryRecord = this.recoveryKey
        ? recovery.getRecord(this.recoveryKey)
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
    phase(): EditVersionCommandsState["localPhase"] {
      const { recovery } = useCommandStores();
      return (
        (this.recoveryKey ? recovery.phases[this.recoveryKey] : null) ??
        this.localPhase
      );
    },
    readbackError(): string | null {
      const { recovery } = useCommandStores();
      return (
        (this.recoveryKey ? recovery.readbackErrors[this.recoveryKey] : null) ??
        null
      );
    },
    storageError(): string | null {
      const { recovery } = useCommandStores();
      return (
        recovery.storageError ??
        (this.recoveryKey ? recovery.contextErrors[this.recoveryKey] : null) ??
        null
      );
    },
    canStartRevert(): boolean {
      const { editor, editorNavigation, editorSession } = useCommandStores();
      return (
        !editorNavigation.logoutAttempt &&
        isAuthenticatedEditor() &&
        !!editorSession.activeWorkspace?.workOrder.editVersion.changeSet &&
        editor.readyFor(
          editorSession.activeWorkspace.workOrder.editVersion.changeSet
            .featureId,
        ) &&
        editorSession.activeWorkspace.workOrder.editVersion
          .hasPersistedChangeSet &&
        !this.storageError &&
        !this.recoveryRecord &&
        !["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
          this.saveError ?? "",
        ) &&
        ["idle", "editing", "rejected"].includes(this.phase)
      );
    },
    canRetryPendingCommand(): boolean {
      const { auth } = useCommandStores();
      return (
        canInteractWithEditVersion(this.storageError) &&
        this.phase === "unknown" &&
        this.recoveryRecord?.state === "unknown" &&
        this.recoveryRecord.command.actorId === auth.user?.id
      );
    },
    canRetryCurrentRead(): boolean {
      const { auth } = useCommandStores();
      return (
        canInteractWithEditVersion(this.storageError) &&
        !!this.readbackError &&
        this.recoveryReadSeq === null &&
        this.phase !== "blocked" &&
        (this.recoveryRecord?.state === "succeeded" ||
          this.recoveryRecord?.state === "rejected") &&
        this.recoveryRecord.command.actorId === auth.user?.id
      );
    },
    canDiscardRejectedAttempt(): boolean {
      return (
        canInteractWithEditVersion(this.storageError) &&
        this.localPhase === "stale" &&
        !this.recoveryRecord &&
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
      return !areGeometryCoordinatesEqual(
        state.commandResult.updatedFeature.geometry,
        state.submittedSourceGeometry,
      );
    },
    pendingCommand(): PendingGeometryCommand | null {
      return this.recoveryRecord?.command ?? null;
    },
  },
  actions: {
    beginRevert(): "resolve-dirty" | "confirm" | "blocked" {
      const { auth, editVersionDraft, editorSession } = useCommandStores();
      if (
        !this.canStartRevert ||
        this.revertConfirmation ||
        !auth.user ||
        this.hasAccessSuspension(auth.user.id)
      )
        return "blocked";
      const workspace = editorSession.activeWorkspace!;
      const version = workspace.workOrder.editVersion;
      const phase =
        editVersionDraft.localDraft &&
        isLocalDraftDirty(editVersionDraft.localDraft)
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
      const { auth, editorSession } = useCommandStores();
      const context = this.revertConfirmation;
      const workspace = editorSession.activeWorkspace;
      return (
        !!context &&
        context.confirmationId === id &&
        this.canStartRevert &&
        auth.user?.id === context.actorId &&
        workspace?.workOrder.id === context.workOrderId &&
        workspace.workOrder.editVersion.id === context.editVersionId &&
        editorSession.openedEditVersionId === context.editVersionId &&
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
      const { editVersionDraft } = useCommandStores();
      if (
        !this.isCurrentRevertConfirmation(id) ||
        this.revertConfirmation?.phase !== "resolve-dirty"
      )
        return false;
      resetLocalEditingState(this);
      editVersionDraft.editBlockReason = null;
      this.revertConfirmation.phase = "confirm";
      return true;
    },
    async confirmRevert(id: string): Promise<void> {
      const { editorSession } = useCommandStores();
      if (
        !this.isCurrentRevertConfirmation(id) ||
        this.revertConfirmation?.phase !== "confirm"
      )
        return;
      const context = this.revertConfirmation;
      if (this.hasAccessSuspension(context.actorId)) return;
      const command = createGeometryCommand({
        actorId: context.actorId,
        target: {
          workOrderId: context.workOrderId,
          editVersionId: context.editVersionId,
          featureId: context.featureId,
        },
        draftVersionToken: context.token,
        geometry:
          editorSession.activeWorkspace!.workOrder.editVersion.changeSet!
            .baselineGeometry,
      });
      this.cancelRevert(id);
      await submitGeometryCommand(this, command);
    },
    attachRecoveryHost(): () => void {
      const { auth, recovery, workOrders, editorNavigation, editorSession } =
        useCommandStores();
      if (recoveryBindings.has(this)) return recoveryBindings.get(this)!;
      const detach = recovery.bindHost({
        session: () => {
          return auth.isAuthenticated && auth.user
            ? {
                actorId: auth.user.id,
                epoch: auth.sessionEpoch,
                canEdit: auth.user.role === "editor",
              }
            : null;
        },
        canAccess: (context) =>
          auth.user?.id === context.actorId &&
          workOrders.items.some((item) => item.id === context.workOrderId),
        reserveRead: (context) => editorSession.reserveWorkspaceRead(context),
        isReadCurrent: (ticket) =>
          editorSession.readGenerations[ticket.key] === ticket.generation,
        applyRead: (ticket, workspace) =>
          editorSession.applyWorkspaceRead(ticket, workspace),
        complete: (completion) => this.completeRecovery(completion),
        interrupted: (key, reason) => {
          if (reason === "session") {
            auth.clearLocalSession();
            return;
          }
          if (editorNavigation.navigation?.sourceKey === key)
            editorNavigation.navigation = null;
          if (reason === "access" && this.recoveryKey === key)
            editorSession.clearOpenedWorkspace({ force: true });
        },
      });
      recoveryBindings.set(this, detach);
      return detach;
    },
    completeRecovery({ record, sessionEpoch }: RecoveryCompletion): void {
      const { editorNavigation } = useCommandStores();
      if (!isCurrentActorSession(record.command.actorId, sessionEpoch)) return;
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
        resetLocalEditingState(this);
        const navigation = editorNavigation.navigation;
        if (
          navigation?.sourceKey === record.key &&
          navigation.commandId === record.command.request.commandId &&
          navigation.sessionEpoch === sessionEpoch
        ) {
          editorNavigation.navigation = null;
          void editorNavigation.performNavigation(navigation.target);
        }
      }
    },
    suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void {
      const { auth, recovery, editorNavigation, editorSession } =
        useCommandStores();
      const actor = actorId ?? auth.user?.id;
      if (actor) void recovery.suspendActor(actor);
      editorNavigation.navigation = null;
      editorSession.clearOpenedWorkspace({ force: true });
    },
    async suspendWorkOrderRecovery(workOrderId: string): Promise<void> {
      const { auth, recovery, editorSession } = useCommandStores();
      const actor = auth.user?.id;
      if (editorSession.openedWorkOrderId === workOrderId)
        editorSession.clearOpenedWorkspace({ force: true });
      if (actor) await recovery.suspendActor(actor, workOrderId);
    },
    hasAccessSuspension(actorId: string): boolean {
      return (
        this.recoveryRecord?.command.actorId === actorId &&
        this.recoveryRecord.state === "blocked"
      );
    },
    async saveLocalDraft(): Promise<void> {
      const {
        auth,
        editor,
        editVersionDraft,
        editorNavigation,
        editorSession,
      } = useCommandStores();
      const user = auth.user;
      const workspace = editorSession.activeWorkspace;
      if (
        !canInteractWithEditVersion(this.storageError) ||
        !user ||
        !workspace ||
        !editVersionDraft.localDraft ||
        !editor.readyFor(editVersionDraft.localDraft.featureId) ||
        !isLocalDraftDirty(editVersionDraft.localDraft) ||
        this.recoveryRecord ||
        !["editing", "rejected"].includes(this.phase)
      )
        return;
      if (
        this.rejectedCandidateGeometry &&
        areGeometryCoordinatesEqual(
          this.rejectedCandidateGeometry,
          editVersionDraft.localDraft.candidateGeometry,
        )
      )
        return;
      const command = createGeometryCommand({
        actorId: user.id,
        target: {
          workOrderId: workspace.workOrder.id,
          editVersionId: workspace.workOrder.editVersion.id,
          featureId: editVersionDraft.localDraft.featureId,
        },
        draftVersionToken: editVersionDraft.localDraft.sourceToken,
        geometry: editVersionDraft.localDraft.candidateGeometry,
      });
      if (editorNavigation.navigation?.phase === "saving")
        editorNavigation.navigation.commandId = command.request.commandId;
      await submitGeometryCommand(this, command);
    },
    async refreshCurrentWorkspace(): Promise<void> {
      const { recovery } = useCommandStores();
      if (this.canRetryCurrentRead && this.recoveryKey)
        await recovery.retryRead(this.recoveryKey);
    },
    async retryPendingSave(): Promise<void> {
      const { recovery, editorNavigation } = useCommandStores();
      if (!editorNavigation.workspaceInteractionLocked && this.recoveryKey)
        await recovery.retry(this.recoveryKey);
    },
    async restorePendingSave(): Promise<void> {
      const { auth, recovery } = useCommandStores();
      this.attachRecoveryHost();
      if (auth.user) await recovery.initializeActor(auth.user.id);
      if (this.recoveryKey && this.staleComparisons[this.recoveryKey]) {
        this.localPhase = "stale";
        this.saveError = "DRAFT_VERSION_STALE";
      }
    },
    discardRejectedAttempt(): boolean {
      const { editVersionDraft } = useCommandStores();
      if (!this.canDiscardRejectedAttempt) return false;
      this.comparisonPreview = null;
      if (this.recoveryKey) delete this.staleComparisons[this.recoveryKey];
      return editVersionDraft.cancelLocalEdit();
    },
  },
});

function useCommandStores() {
  return {
    get auth() {
      return useAuthStore();
    },
    get recovery() {
      return useWorkspaceRecoveryStore();
    },
    get editor() {
      return useEditVersionEditor();
    },
    get editVersionDraft() {
      return useEditVersionDraftStore();
    },
    get workOrders() {
      return useWorkOrdersStore();
    },
    get editorNavigation() {
      return useEditorNavigationStore();
    },
    get editorSession() {
      return useEditorSessionStore();
    },
  };
}

function canInteractWithEditVersion(storageError: string | null): boolean {
  const { editorNavigation, editorSession } = useCommandStores();
  return (
    !editorNavigation.workspaceInteractionLocked &&
    isAuthenticatedEditor() &&
    !!editorSession.activeWorkspace &&
    !storageError
  );
}

function isAuthenticatedEditor(): boolean {
  const { auth } = useCommandStores();
  return auth.isAuthenticated && auth.user?.role === "editor";
}

function isCurrentActorSession(actorId: string, sessionEpoch: number): boolean {
  const { auth } = useCommandStores();
  return auth.user?.id === actorId && auth.sessionEpoch === sessionEpoch;
}

function areGeometryCoordinatesEqual(
  first: LineStringXY,
  second: LineStringXY,
): boolean {
  return (
    JSON.stringify(first.coordinates) === JSON.stringify(second.coordinates)
  );
}

function findFeatureLineGeometry(
  workspace: WorkspaceResponse | null,
  featureId: string,
): LineStringXY | null {
  const geometry = workspace?.workOrder.editVersion.features.features.find(
    (feature) => feature.id === featureId,
  )?.geometry;
  return isLineStringXY(geometry) ? geometry : null;
}

function createGeometryCommand({
  actorId,
  target,
  draftVersionToken,
  geometry,
}: {
  actorId: string;
  target: SaveTarget;
  draftVersionToken: string;
  geometry: LineStringXY;
}): PendingGeometryCommand {
  return {
    actorId,
    target,
    request: {
      commandId: crypto.randomUUID(),
      draftVersionToken,
      geometry: copyGeometry(geometry),
    },
  };
}

function resetLocalEditingState(
  store: ReturnType<typeof useEditVersionCommandsStore>,
): void {
  const { editVersionDraft } = useCommandStores();
  editVersionDraft.localDraft = null;
  store.rejectedCandidateGeometry = null;
  store.saveError = null;
  store.localPhase = "idle";
}

async function submitGeometryCommand(
  store: ReturnType<typeof useEditVersionCommandsStore>,
  command: PendingGeometryCommand,
): Promise<void> {
  const { auth, recovery, editVersionDraft, editorNavigation, editorSession } =
    useCommandStores();
  const workspace = editorSession.activeWorkspace;
  const submitEpoch = auth.sessionEpoch;
  if (!workspace) return;
  const geometry = findFeatureLineGeometry(workspace, command.target.featureId);
  if (!geometry) return;
  const vertexIndex =
    editVersionDraft.localDraft?.vertexIndex ??
    workspace.workOrder.editVersion.changeSet?.vertexIndex;
  if (vertexIndex === undefined) return;
  const source = { geometry: copyGeometry(geometry), vertexIndex };
  store.localPhase = "sending";
  store.attachRecoveryHost();
  await recovery.initializeActor(command.actorId);
  if (
    !isCurrentActorSession(command.actorId, submitEpoch) ||
    editorSession.openedWorkOrderId !== command.target.workOrderId ||
    editorSession.openedEditVersionId !== command.target.editVersionId
  )
    return;
  if (editorNavigation.logoutAttempt) {
    store.localPhase = "editing";
    return;
  }
  store.submittedSourceGeometry = source.geometry;
  store.submittedCommandId = command.request.commandId;
  store.commandResult = null;
  store.saveError = null;
  store.rejectedCandidateGeometry = null;
  const started = await recovery.submit(command, source);
  if (
    started === "blocked" &&
    auth.user?.id === command.actorId &&
    editorSession.openedEditVersionId === command.target.editVersionId
  ) {
    store.localPhase = store.storageError ? "blocked" : "editing";
    editorNavigation.navigation = null;
  }
}
