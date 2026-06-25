import { defineStore } from "pinia";

import {
  fetchAssignedWorkOrders,
  fetchWorkspace,
  openEditVersion,
} from "@/api/workOrders";
import type {
  WorkOrderStatus,
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";

type WorkOrdersState = {
  items: WorkOrderSummary[];
  isLoading: boolean;
  errorMessage: string | null;
  selectedWorkOrderId: string | null;
  openedWorkOrderId: string | null;
  openedEditVersionId: string | null;
  workspace: WorkspaceResponse | null;
  isOpeningWorkspace: boolean;
  openWorkspaceErrorByWorkOrderId: Record<string, string | undefined>;
  lastFittedWorkspaceKey: string | null;
  openWorkspaceRequestSeq: number;
};

export const useWorkOrdersStore = defineStore("workOrders", {
  state: (): WorkOrdersState => ({
    items: [],
    isLoading: false,
    errorMessage: null,
    selectedWorkOrderId: null,
    openedWorkOrderId: null,
    openedEditVersionId: null,
    workspace: null,
    isOpeningWorkspace: false,
    openWorkspaceErrorByWorkOrderId: {},
    lastFittedWorkspaceKey: null,
    openWorkspaceRequestSeq: 0,
  }),
  getters: {
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
  },
  actions: {
    async loadAssigned() {
      this.isLoading = true;
      this.errorMessage = null;
      try {
        const result = await fetchAssignedWorkOrders();
        this.items = result.workOrders;
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        ) {
          this.selectedWorkOrderId = null;
          this.clearOpenedWorkspace();
        }
        if (
          this.openedWorkOrderId &&
          !this.items.some((item) => item.id === this.openedWorkOrderId)
        ) {
          this.clearOpenedWorkspace();
        }
      } catch {
        this.items = [];
        this.errorMessage =
          "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.";
      } finally {
        this.isLoading = false;
      }
    },
    selectWorkOrder(workOrderId: string) {
      this.selectedWorkOrderId = workOrderId;
    },
    clearSelection() {
      this.selectedWorkOrderId = null;
      this.clearOpenedWorkspace();
    },
    async openSelectedWorkOrder() {
      const workOrderId = this.selectedWorkOrderId;
      if (!workOrderId || this.isOpeningWorkspace) {
        return;
      }

      const requestSeq = this.openWorkspaceRequestSeq + 1;
      this.openWorkspaceRequestSeq = requestSeq;
      this.isOpeningWorkspace = true;
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
        [workOrderId]: undefined,
      };

      try {
        const openResult = await openEditVersion(workOrderId);
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
      } catch {
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          this.openWorkspaceErrorByWorkOrderId = {
            ...this.openWorkspaceErrorByWorkOrderId,
            [workOrderId]:
              "Не удалось открыть рабочую версию. Обновите список или попробуйте еще раз.",
          };
        }
      } finally {
        if (this.openWorkspaceRequestSeq === requestSeq) {
          this.isOpeningWorkspace = false;
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
    updateWorkOrderStatus(workOrderId: string, status: WorkOrderStatus): void {
      this.items = this.items.map((item) =>
        item.id === workOrderId ? { ...item, status } : item,
      );
    },
    clearOpenedWorkspace(): void {
      this.openedWorkOrderId = null;
      this.openedEditVersionId = null;
      this.workspace = null;
      this.lastFittedWorkspaceKey = null;
    },
  },
});
