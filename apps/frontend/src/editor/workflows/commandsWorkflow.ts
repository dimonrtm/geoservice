import type { WorkspaceResponse } from "@/contracts/work_order/work-orders";
import {
  copyGeometry,
  isLineStringXY,
  type LineStringXY,
  type PendingGeometryCommand,
  type SaveTarget,
  type WorkspaceRecoveryRecord,
} from "@/contracts/workspace/workspace-edit";
import {
  recoveryKey,
  type RecoveryCompletion,
} from "@/contracts/workspace/workspace-recovery";
import { isLocalDraftDirty } from "@/domain/workspace/workspaceDraft";
import type {
  CommandsPort,
  EditVersionCommandsState,
} from "../contracts/commands";
import { sameDraft, sameEditorContext } from "../editorWorkflowContracts";
import type { SaveStartResult } from "../editorWorkflowContracts";
import type { EditorWorkflowPorts } from "../editorWorkflowPorts";
export function createCommandsWorkflow(ports: EditorWorkflowPorts) {
  const store = ports.editVersionCommands;
  const confirmationWatchers = new WeakMap<object, () => void>();
  const recoveryBindings = new WeakMap<object, () => void>();
  const watch = ports.watchConfirmation;
  function get_recoveryKey(): string | null {
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
  }
  function get_activeComparison():
    | EditVersionCommandsState["staleComparisons"][string]
    | null {
    const key = store.recoveryKey;
    return key ? (store.staleComparisons[key] ?? null) : null;
  }
  function get_previewGeometry(): LineStringXY | null {
    const { editorSession } = useCommandStores();
    const material = store.activeComparison;
    if (!material || !store.comparisonPreview) return null;
    if (store.comparisonPreview === "source")
      return material.source?.geometry ?? null;
    if (store.comparisonPreview === "candidate") return material.candidate;
    return findFeatureLineGeometry(
      editorSession.activeWorkspace,
      material.featureId,
    );
  }
  function get_recoveryRecord(): WorkspaceRecoveryRecord | null {
    const { recovery } = useCommandStores();
    const recoveryRecord = store.recoveryKey
      ? recovery.getRecord(store.recoveryKey)
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
  }
  function get_phase(): EditVersionCommandsState["localPhase"] {
    const { recovery } = useCommandStores();
    return (
      (store.recoveryKey ? recovery.phases[store.recoveryKey] : null) ??
      store.localPhase
    );
  }
  function get_readbackError(): string | null {
    const { recovery } = useCommandStores();
    return (
      (store.recoveryKey ? recovery.readbackErrors[store.recoveryKey] : null) ??
      null
    );
  }
  function get_storageError(): string | null {
    const { recovery } = useCommandStores();
    return (
      recovery.storageError ??
      (store.recoveryKey ? recovery.contextErrors[store.recoveryKey] : null) ??
      null
    );
  }
  function get_canStartRevert(): boolean {
    const { editor, editorNavigation, editorSession } = useCommandStores();
    return (
      !editorNavigation.logoutAttempt &&
      isAuthenticatedEditor() &&
      !!editorSession.activeWorkspace?.workOrder.editVersion.changeSet &&
      editor.readyFor(
        editorSession.activeWorkspace.workOrder.editVersion.changeSet.featureId,
      ) &&
      editorSession.activeWorkspace.workOrder.editVersion
        .hasPersistedChangeSet &&
      !store.storageError &&
      !store.recoveryRecord &&
      !["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
        store.saveError ?? "",
      ) &&
      ["idle", "editing", "rejected"].includes(store.phase)
    );
  }
  function get_canRetryPendingCommand(): boolean {
    const { auth } = useCommandStores();
    return (
      canInteractWithEditVersion(store.storageError) &&
      store.phase === "unknown" &&
      store.recoveryRecord?.state === "unknown" &&
      store.recoveryRecord.command.actorId === auth.user?.id
    );
  }
  function get_canRetryCurrentRead(): boolean {
    const { auth } = useCommandStores();
    return (
      canInteractWithEditVersion(store.storageError) &&
      !!store.readbackError &&
      store.recoveryReadSeq === null &&
      store.phase !== "blocked" &&
      (store.recoveryRecord?.state === "succeeded" ||
        store.recoveryRecord?.state === "rejected") &&
      store.recoveryRecord.command.actorId === auth.user?.id
    );
  }
  function get_canDiscardRejectedAttempt(): boolean {
    return (
      canInteractWithEditVersion(store.storageError) &&
      store.localPhase === "stale" &&
      !store.recoveryRecord &&
      !store.readbackError
    );
  }
  function get_didSaveChangeGeometry(): boolean | null {
    if (
      !store.commandResult ||
      !store.submittedSourceGeometry ||
      store.commandResult.commandId !== store.submittedCommandId
    )
      return null;
    return !areGeometryCoordinatesEqual(
      store.commandResult.updatedFeature.geometry,
      store.submittedSourceGeometry,
    );
  }
  function get_pendingCommand(): PendingGeometryCommand | null {
    return store.recoveryRecord?.command ?? null;
  }
  function beginRevert(): "resolve-dirty" | "confirm" | "blocked" {
    const { auth, editVersionDraft, editorSession } = useCommandStores();
    if (
      !store.canStartRevert ||
      store.revertConfirmation ||
      !auth.user ||
      store.hasAccessSuspension(auth.user.id)
    )
      return "blocked";
    const workspace = editorSession.activeWorkspace!;
    const version = workspace.workOrder.editVersion;
    const phase =
      editVersionDraft.localDraft &&
      isLocalDraftDirty(editVersionDraft.localDraft)
        ? "resolve-dirty"
        : "confirm";
    const confirmationId = ports.createCommandId();
    store.startRevertConfirmation({
      confirmationId,
      actorId: auth.user.id,
      workOrderId: workspace.workOrder.id,
      editVersionId: version.id,
      featureId: version.changeSet!.featureId,
      token: version.draftVersionToken,
      phase,
    });
    confirmationWatchers.get(store)?.();
    confirmationWatchers.set(
      store,
      watch(
        () => store.isCurrentRevertConfirmation(confirmationId),
        (valid) => {
          if (!valid) store.cancelRevert(confirmationId);
        },
        { flush: "sync" },
      ),
    );
    return phase;
  }
  function isCurrentRevertConfirmation(id: string): boolean {
    const { auth, editorSession } = useCommandStores();
    const context = store.revertConfirmation;
    const workspace = editorSession.activeWorkspace;
    return (
      !!context &&
      context.confirmationId === id &&
      store.canStartRevert &&
      auth.user?.id === context.actorId &&
      workspace?.workOrder.id === context.workOrderId &&
      workspace.workOrder.editVersion.id === context.editVersionId &&
      editorSession.openedEditVersionId === context.editVersionId &&
      workspace.workOrder.editVersion.draftVersionToken === context.token &&
      workspace.workOrder.editVersion.changeSet?.featureId === context.featureId
    );
  }
  function cancelRevert(id: string): void {
    if (store.revertConfirmation?.confirmationId !== id) return;
    confirmationWatchers.get(store)?.();
    confirmationWatchers.delete(store);
    store.finishRevertConfirmation(id);
  }
  function discardLocalDraftForRevert(id: string): boolean {
    const { editVersionDraft } = useCommandStores();
    if (
      !store.isCurrentRevertConfirmation(id) ||
      store.revertConfirmation?.phase !== "resolve-dirty"
    )
      return false;
    resetLocalEditingState(store);
    editVersionDraft.reportEditBlocked(null);
    store.resolveRevertDraft(id);
    return true;
  }
  async function confirmRevert(id: string): Promise<void> {
    const { editorSession } = useCommandStores();
    if (
      !store.isCurrentRevertConfirmation(id) ||
      store.revertConfirmation?.phase !== "confirm"
    )
      return;
    const context = store.revertConfirmation;
    if (store.hasAccessSuspension(context.actorId)) return;
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
    const submissionContext = ports.context();
    if (!submissionContext) return;
    store.captureSaveAttempt({
      context: submissionContext,
      draftIdentity: ports.editVersionDraft.draftIdentity,
      commandId: command.request.commandId,
      navigationId: null,
    });
    store.cancelRevert(id);
    await submitGeometryCommand(store, command);
  }
  function attachRecoveryHost(): () => void {
    const { auth, recovery, workOrders, editorNavigation, editorSession } =
      useCommandStores();
    if (recoveryBindings.has(store)) return recoveryBindings.get(store)!;
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
      complete: (completion) => store.completeRecovery(completion),
      interrupted: (key, reason) => {
        if (reason === "session") {
          auth.clearLocalSession();
          return;
        }
        if (editorNavigation.navigation?.sourceKey === key)
          editorNavigation.abortNavigation(editorNavigation.navigation!.id);
        if (reason === "access" && store.recoveryKey === key)
          editorSession.clearOpenedWorkspace({ force: true });
      },
    });
    recoveryBindings.set(store, detach);
    return detach;
  }
  function completeRecovery(completion: RecoveryCompletion): void {
    const { record, sessionEpoch } = completion;
    if (!isCurrentActorSession(record.command.actorId, sessionEpoch)) return;
    const current = ports.context();
    const attempt = store.activeSaveAttempt;
    const selected = store.recoveryKey === record.key;
    const matchingAttempt =
      attempt?.commandId === record.command.request.commandId;
    const foreground =
      selected &&
      (!attempt ||
        matchingAttempt ||
        !current ||
        !sameEditorContext(attempt.context, current)) &&
      (!ports.editVersionDraft.draftIdentity ||
        (matchingAttempt &&
          !!attempt.draftIdentity &&
          sameDraft(
            ports.editVersionDraft.draftIdentity,
            attempt.draftIdentity,
          ))) &&
      (!matchingAttempt ||
        (!!current && sameEditorContext(attempt.context, current)));
    if (record.outcome.kind === "rejected") {
      store.acceptRejectedRecovery(completion, foreground);
      return;
    }
    if (record.outcome.kind !== "succeeded" || !foreground) return;
    store.acceptSuccessfulRecovery(completion);
    if (matchingAttempt && attempt.draftIdentity)
      ports.editVersionDraft.finishDraft(attempt.draftIdentity);
    if (matchingAttempt) {
      const target = ports.editorNavigation.takeCompletedNavigation(attempt);
      if (target) void ports.editorNavigation.performNavigation(target);
    }
  }
  function suspendWorkspaceRecoveryForAccessLoss(actorId?: string): void {
    const { auth, recovery, editorNavigation, editorSession } =
      useCommandStores();
    const actor = actorId ?? auth.user?.id;
    if (actor) void recovery.suspendActor(actor);
    if (editorNavigation.navigation)
      editorNavigation.abortNavigation(editorNavigation.navigation.id);
    editorSession.clearOpenedWorkspace({ force: true });
  }
  async function suspendWorkOrderRecovery(workOrderId: string): Promise<void> {
    const { auth, recovery, editorSession } = useCommandStores();
    const actor = auth.user?.id;
    if (editorSession.openedWorkOrderId === workOrderId)
      editorSession.clearOpenedWorkspace({ force: true });
    if (actor) await recovery.suspendActor(actor, workOrderId);
  }
  function hasAccessSuspension(actorId: string): boolean {
    return (
      store.recoveryRecord?.command.actorId === actorId &&
      store.recoveryRecord.state === "blocked"
    );
  }
  async function saveLocalDraft(): Promise<SaveStartResult> {
    const { auth, editor, editVersionDraft, editorNavigation, editorSession } =
      useCommandStores();
    const user = auth.user;
    const workspace = editorSession.activeWorkspace;
    if (
      !canInteractWithEditVersion(store.storageError) ||
      !user ||
      !workspace ||
      !editVersionDraft.localDraft ||
      !editor.readyFor(editVersionDraft.localDraft.featureId) ||
      !isLocalDraftDirty(editVersionDraft.localDraft) ||
      store.recoveryRecord ||
      !["editing", "rejected"].includes(store.phase)
    )
      return { kind: "not-started" };
    if (
      store.rejectedCandidateGeometry &&
      areGeometryCoordinatesEqual(
        store.rejectedCandidateGeometry,
        editVersionDraft.localDraft.candidateGeometry,
      )
    )
      return { kind: "not-started" };
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
    const context = ports.context();
    if (!context) return { kind: "not-started" };
    const attempt = {
      context,
      draftIdentity: editVersionDraft.draftIdentity,
      commandId: command.request.commandId,
      navigationId:
        editorNavigation.navigation?.phase === "saving"
          ? editorNavigation.navigation.id
          : null,
    };
    store.captureSaveAttempt(attempt);
    if (attempt.navigationId)
      editorNavigation.bindNavigationSave(attempt.navigationId, attempt);
    return submitGeometryCommand(store, command);
  }
  async function refreshCurrentWorkspace(): Promise<void> {
    const { recovery } = useCommandStores();
    if (store.canRetryCurrentRead && store.recoveryKey)
      await recovery.retryRead(store.recoveryKey);
  }
  async function retryPendingSave(): Promise<void> {
    const { recovery, editorNavigation } = useCommandStores();
    if (!editorNavigation.workspaceInteractionLocked && store.recoveryKey)
      await recovery.retry(store.recoveryKey);
  }
  async function restorePendingSave(): Promise<void> {
    const { auth, recovery } = useCommandStores();
    store.attachRecoveryHost();
    if (auth.user) await recovery.initializeActor(auth.user.id);
    if (store.recoveryKey && store.staleComparisons[store.recoveryKey]) {
      store.restoreStaleComparison();
    }
  }
  function discardRejectedAttempt(): boolean {
    const { editVersionDraft } = useCommandStores();
    if (!store.canDiscardRejectedAttempt) return false;
    store.hideComparisonPreview();
    if (store.recoveryKey) store.removeStaleComparison(store.recoveryKey);
    return editVersionDraft.cancelLocalEdit();
  }
  function useCommandStores() {
    return ports;
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
  function isCurrentActorSession(
    actorId: string,
    sessionEpoch: number,
  ): boolean {
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
        commandId: ports.createCommandId(),
        draftVersionToken,
        geometry: copyGeometry(geometry),
      },
    };
  }
  function resetLocalEditingState(store: CommandsPort): void {
    const { editVersionDraft } = useCommandStores();
    editVersionDraft.resetDraftState();
    store.finishLocalEditing();
  }
  async function submitGeometryCommand(
    store: CommandsPort,
    command: PendingGeometryCommand,
  ): Promise<SaveStartResult> {
    const {
      auth,
      recovery,
      editVersionDraft,
      editorNavigation,
      editorSession,
    } = useCommandStores();
    const workspace = editorSession.activeWorkspace;
    const submitEpoch = auth.sessionEpoch;
    const submitContext = ports.context();
    const navigationId = editorNavigation.navigation?.id;
    if (!workspace || !submitContext) return { kind: "not-started" };
    const geometry = findFeatureLineGeometry(
      workspace,
      command.target.featureId,
    );
    if (!geometry) return { kind: "not-started" };
    const vertexIndex =
      editVersionDraft.localDraft?.vertexIndex ??
      workspace.workOrder.editVersion.changeSet?.vertexIndex;
    if (vertexIndex === undefined) return { kind: "not-started" };
    const source = { geometry: copyGeometry(geometry), vertexIndex };
    store.reserveSubmission();
    store.attachRecoveryHost();
    await recovery.initializeActor(command.actorId);
    if (
      !isCurrentActorSession(command.actorId, submitEpoch) ||
      editorSession.openedWorkOrderId !== command.target.workOrderId ||
      editorSession.openedEditVersionId !== command.target.editVersionId ||
      !ports.context() ||
      !sameEditorContext(submitContext, ports.context()!)
    )
      return { kind: "superseded" };
    if (editorNavigation.logoutAttempt) {
      store.markLocalEditing();
      return { kind: "not-started" };
    }
    store.recordSubmission(command.request.commandId, source.geometry);
    const started = await recovery.submit(command, source);
    if (
      started === "blocked" &&
      auth.user?.id === command.actorId &&
      editorSession.openedEditVersionId === command.target.editVersionId &&
      !!ports.context() &&
      sameEditorContext(submitContext, ports.context()!)
    ) {
      store.submissionBlocked(!!store.storageError);
      if (navigationId) editorNavigation.abortNavigation(navigationId);
    }
    if (!ports.context() || !sameEditorContext(submitContext, ports.context()!))
      return { kind: "superseded" };
    return started === "started"
      ? { kind: "started", commandId: command.request.commandId }
      : { kind: "not-started" };
  }
  return {
    actions: {
      beginRevert,
      isCurrentRevertConfirmation,
      cancelRevert,
      discardLocalDraftForRevert,
      confirmRevert,
      attachRecoveryHost,
      completeRecovery,
      suspendWorkspaceRecoveryForAccessLoss,
      suspendWorkOrderRecovery,
      hasAccessSuspension,
      saveLocalDraft,
      refreshCurrentWorkspace,
      retryPendingSave,
      restorePendingSave,
      discardRejectedAttempt,
    },
    getters: {
      recoveryKey: get_recoveryKey,
      activeComparison: get_activeComparison,
      previewGeometry: get_previewGeometry,
      recoveryRecord: get_recoveryRecord,
      phase: get_phase,
      readbackError: get_readbackError,
      storageError: get_storageError,
      canStartRevert: get_canStartRevert,
      canRetryPendingCommand: get_canRetryPendingCommand,
      canRetryCurrentRead: get_canRetryCurrentRead,
      canDiscardRejectedAttempt: get_canDiscardRejectedAttempt,
      didSaveChangeGeometry: get_didSaveChangeGeometry,
      pendingCommand: get_pendingCommand,
    },
  };
}
