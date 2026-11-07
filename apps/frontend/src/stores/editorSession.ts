import { defineStore } from "pinia";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import {
  recoveryKey,
  type RecoveryContext,
  type ReadTicket,
  type RecoveryApplyResult,
} from "@/contracts/workspace-recovery";

import { parseApiError } from "@/api/parseApiError";
import type { ErrorPresentation, ParsedApiError } from "@/contracts/api-error";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import {
  presentWorkspaceOpenError,
  presentWorkspaceRestoreError,
} from "@/errors/apiErrorPresentations";
import { openEditVersion } from "@/api/editVersions";
import { useEditVersionEditor } from "@/composables/useEditVersionEditor";
import { useEditVersionDraftStore } from "@/stores/editVersionDraft";
import { useEditVersionCommandsStore } from "@/stores/editVersionCommands";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useEditorNavigationStore } from "@/stores/editorNavigation";
import {
  readStoredSelectedWorkOrder,
  readStoredOpenedWorkspace,
  storeOpenedWorkspace,
  clearStoredOpenedWorkspace,
  type ResetWorkOrdersOptions,
} from "./editorSessionStorage";
type WorkspaceErrorOperation = "open" | "restore";

type ClearOpenedWorkspaceOptions = {
  preserveStoredWorkspace?: boolean;
  force?: boolean;
};
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

type EditorSessionState = {
  readGenerations: Record<string, number>;
  openedWorkOrderId: string | null;
  openedEditVersionId: string | null;
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
  openWorkspaceRequestSeq: number;
};

export const useEditorSessionStore = defineStore("editorSession", {
  state: (): EditorSessionState => ({
    readGenerations: {},
    openedWorkOrderId: null,
    openedEditVersionId: null,
    openingWorkOrderId: null,
    openingEditVersionId: null,
    workspaceReadIntent: null,
    openingWorkspaceRequestSeq: null,
    openWorkspaceErrorByWorkOrderId: {},
    openWorkspaceErrorOperationByWorkOrderId: {},
    openWorkspaceRequestSeq: 0,
  }),
  getters: {
    isOpeningWorkspace: (state) => state.openingWorkOrderId !== null,
    activeWorkspace(): WorkspaceResponse | null {
      if (
        !this.openedWorkOrderId ||
        this.openedWorkOrderId !== useWorkOrdersStore().selectedWorkOrderId
      )
        return null;
      return useEditVersionEditor().snapshot;
    },
    activeWorkspaceKey: (state) => {
      const workOrders = useWorkOrdersStore();
      if (
        workOrders.selectedWorkOrderId === null ||
        state.openedWorkOrderId !== workOrders.selectedWorkOrderId ||
        state.openedEditVersionId === null
      ) {
        return null;
      }
      return `${state.openedWorkOrderId}:${state.openedEditVersionId}`;
    },
    selectedOpenWorkspaceError: (state) => {
      return getSelectedWorkOrderValue(state.openWorkspaceErrorByWorkOrderId);
    },
    selectedOpenWorkspaceErrorOperation: (state) => {
      return getSelectedWorkOrderValue(
        state.openWorkspaceErrorOperationByWorkOrderId,
      );
    },
  },
  actions: {
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
      const workOrders = useWorkOrdersStore();
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
      if (!isCurrentWorkspaceRead(this, ticket)) return "superseded";
      if (
        this.workspaceReadIntent?.key === ticket.key &&
        this.workspaceReadIntent.openSeq === this.openWorkspaceRequestSeq &&
        workOrders.selectedWorkOrderId === workspace.workOrder.id
      ) {
        setOpenedVersion(
          this,
          workspace.workOrder.id,
          workspace.workOrder.editVersion.id,
        );
        storeOpenedWorkspace({
          workOrderId: workspace.workOrder.id,
          editVersionId: workspace.workOrder.editVersion.id,
        });
      }
      if (
        this.openedWorkOrderId === workspace.workOrder.id &&
        this.openedEditVersionId === workspace.workOrder.editVersion.id
      )
        useEditVersionEditor().applyReadback(workspace);
      return "applied";
    },
    async openSelectedWorkOrder(): Promise<void> {
      const workOrderId = useWorkOrdersStore().selectedWorkOrderId;
      if (workOrderId) await this.loadVersion(workOrderId);
    },
    async restoreOpenedWorkspace(): Promise<void> {
      const workOrders = useWorkOrdersStore();
      const editVersionCommands = useEditVersionCommandsStore();
      if (!canLoadVersion(this)) return;
      const storedSelection = readStoredSelectedWorkOrder();
      const storedWorkspace = readStoredOpenedWorkspace();
      const workOrderId =
        workOrders.selectedWorkOrderId ??
        storedSelection?.workOrderId ??
        storedWorkspace?.workOrderId ??
        null;

      if (!workOrderId) {
        return;
      }

      if (!isWorkOrderAssigned(workOrderId)) {
        const suspension =
          editVersionCommands.suspendWorkOrderRecovery(workOrderId);
        workOrders.clearSelection();
        this.clearOpenedWorkspace({ force: true });
        await suspension;
        return;
      }

      workOrders.selectWorkOrder(workOrderId);

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

      await this.loadVersion(workOrderId, storedWorkspace.editVersionId);
    },
    async loadVersion(
      workOrderId: string,
      storedVersionId?: string,
    ): Promise<void> {
      if (!canLoadVersion(this)) return;
      const orders = useWorkOrdersStore();
      const commands = useEditVersionCommandsStore();
      const auth = useAuthStore();
      const epoch = auth.sessionEpoch;
      const requestSeq = ++this.openWorkspaceRequestSeq;
      this.openingWorkOrderId = workOrderId;
      this.openingEditVersionId = storedVersionId ?? null;
      this.openingWorkspaceRequestSeq = requestSeq;
      delete this.openWorkspaceErrorByWorkOrderId[workOrderId];
      delete this.openWorkspaceErrorOperationByWorkOrderId[workOrderId];

      let ticket: ReadTicket | null = null;
      const isCurrent = () =>
        auth.sessionEpoch === epoch &&
        this.openWorkspaceRequestSeq === requestSeq &&
        orders.selectedWorkOrderId === workOrderId &&
        (!ticket || isCurrentWorkspaceRead(this, ticket));
      try {
        const editVersionId =
          storedVersionId ??
          (await openEditVersion(workOrderId)).editVersion.id;
        if (!isCurrent() || !auth.user) return;
        if (!storedVersionId)
          orders.updateWorkOrderStatus(workOrderId, "in_progress");
        this.openingEditVersionId = editVersionId;
        ticket = this.reserveWorkspaceRead({
          actorId: auth.user.id,
          workOrderId,
          editVersionId,
        });
        this.workspaceReadIntent = { key: ticket.key, openSeq: requestSeq };
        await useEditVersionEditor().open(
          workOrderId,
          editVersionId,
          (editVersionMap) => {
            if (!isCurrent()) return;
            setOpenedVersion(this, workOrderId, editVersionId);
            orders.updateWorkOrderStatus(
              workOrderId,
              editVersionMap.workOrder.status,
            );
            storeOpenedWorkspace({ workOrderId, editVersionId });
          },
        );
        if (isCurrent() && this.openedEditVersionId === editVersionId)
          await commands.restorePendingSave();
      } catch (error) {
        if (!isCurrent()) return;
        const parsed = parseApiError(error);
        const presentation = storedVersionId
          ? presentWorkspaceRestoreError(parsed)
          : presentWorkspaceOpenError(parsed);
        setWorkspaceError(
          this,
          workOrderId,
          presentation,
          presentation ? (storedVersionId ? "restore" : "open") : undefined,
        );
        if (isWorkspaceAccessFailure(parsed)) {
          this.clearOpenedWorkspace({ force: true });
          await commands.suspendWorkOrderRecovery(workOrderId);
        } else if (storedVersionId) {
          this.clearOpenedWorkspace({
            preserveStoredWorkspace: shouldPreserveStoredWorkspace(parsed),
          });
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
        this.activeWorkspace !== null &&
        this.openedEditVersionId !== null
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
      const editorNavigation = useEditorNavigationStore();
      if (!editorNavigation.allowWorkspaceNavigation()) return;
      clearStoredOpenedWorkspace();
      await this.openSelectedWorkOrder();
    },
    clearOpenedWorkspace(options: ClearOpenedWorkspaceOptions = {}): void {
      const editorNavigation = useEditorNavigationStore();
      const editVersionCommands = useEditVersionCommandsStore();
      const editVersionDraft = useEditVersionDraftStore();
      if (!options.force && !editorNavigation.allowWorkspaceNavigation())
        return;
      this.openWorkspaceRequestSeq++;
      this.workspaceReadIntent = null;
      editVersionCommands.comparisonPreview = null;
      editVersionCommands.submittedSourceGeometry = null;
      editVersionCommands.submittedCommandId = null;
      editVersionCommands.rejectedCandidateGeometry = null;
      editVersionDraft.localDraft = null;
      editVersionCommands.localPhase = "idle";
      editVersionCommands.saveError = null;
      if (options.force) {
        editVersionCommands.commandResult = null;
      }
      setOpenedVersion(this, null, null);
      useEditVersionEditor().reset();
      if (!options.preserveStoredWorkspace) {
        clearStoredOpenedWorkspace();
      }
    },
    resetEditor(options: ResetWorkOrdersOptions = {}): void {
      const commands = useEditVersionCommandsStore();
      if (commands.revertConfirmation)
        commands.cancelRevert(commands.revertConfirmation.confirmationId);
      const generation = this.openWorkspaceRequestSeq + 1;
      this.$reset();
      this.openWorkspaceRequestSeq = generation;
      commands.$reset();
      useEditVersionDraftStore().$reset();
      useEditorNavigationStore().$reset();
      useEditVersionEditor().reset();
      if (!options.preserveOpenedWorkspace) clearStoredOpenedWorkspace();
    },
    async readActiveFeature(featureId?: string): Promise<void> {
      const editor = useEditVersionEditor();
      const workOrderId = this.openedWorkOrderId;
      const generation = this.openWorkspaceRequestSeq;
      if (!workOrderId) return;
      try {
        if (featureId === undefined) await editor.retry();
        else await editor.selectFeature(featureId);
      } catch (error) {
        if (
          generation !== this.openWorkspaceRequestSeq ||
          this.openedWorkOrderId !== workOrderId
        )
          return;
        const parsed = parseApiError(error);
        if (isWorkspaceAccessFailure(parsed)) {
          setWorkspaceError(
            this,
            workOrderId,
            presentWorkspaceRestoreError(parsed),
            "restore",
          );
          await useEditVersionCommandsStore().suspendWorkOrderRecovery(
            workOrderId,
          );
        }
      }
    },
    async reconcileAssignments(): Promise<void> {
      const editVersionCommands = useEditVersionCommandsStore();
      const auth = useAuthStore();
      const epoch = auth.sessionEpoch;
      const actor = auth.user;
      const orders = useWorkOrdersStore();
      const generation = orders.loadAssignedRequestSeq;
      const isCurrent = () =>
        epoch === auth.sessionEpoch &&
        generation === orders.loadAssignedRequestSeq;
      if (!actor || actor.role !== "editor") return;
      if (orders.loadError) {
        if (orders.loadAccessDenied)
          editVersionCommands.suspendWorkspaceRecoveryForAccessLoss();
        return;
      }
      editVersionCommands.attachRecoveryHost();
      const recovery = useWorkspaceRecoveryStore();
      for (const record of Object.values(recovery.records)) {
        if (!isCurrent()) return;
        if (
          record.command.actorId === actor.id &&
          !isWorkOrderAssigned(record.command.target.workOrderId)
        )
          await recovery.suspend(record.key);
      }
      if (!isCurrent()) return;
      if (
        this.openedWorkOrderId &&
        !isWorkOrderAssigned(this.openedWorkOrderId)
      )
        this.clearOpenedWorkspace({ force: true });
      await recovery.initializeActor(actor.id);
    },
  },
});

function getSelectedWorkOrderValue<T>(
  valuesByWorkOrderId: Record<string, T | undefined>,
): T | null {
  const { selectedWorkOrderId } = useWorkOrdersStore();
  return selectedWorkOrderId
    ? (valuesByWorkOrderId[selectedWorkOrderId] ?? null)
    : null;
}

function canLoadVersion(state: EditorSessionState): boolean {
  return (
    useEditorNavigationStore().allowWorkspaceNavigation() &&
    state.openingWorkOrderId === null
  );
}

function isCurrentWorkspaceRead(
  state: EditorSessionState,
  ticket: ReadTicket,
): boolean {
  return state.readGenerations[ticket.key] === ticket.generation;
}

function isWorkOrderAssigned(workOrderId: string): boolean {
  return useWorkOrdersStore().items.some((item) => item.id === workOrderId);
}

function setOpenedVersion(
  state: EditorSessionState,
  workOrderId: string | null,
  editVersionId: string | null,
): void {
  state.openedWorkOrderId = workOrderId;
  state.openedEditVersionId = editVersionId;
}

function setWorkspaceError(
  state: EditorSessionState,
  workOrderId: string,
  presentation: ErrorPresentation | null | undefined,
  operation: WorkspaceErrorOperation | undefined,
): void {
  state.openWorkspaceErrorByWorkOrderId[workOrderId] =
    presentation ?? undefined;
  state.openWorkspaceErrorOperationByWorkOrderId[workOrderId] = operation;
}
