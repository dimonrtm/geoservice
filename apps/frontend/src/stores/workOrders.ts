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
  loadAssignedRequestSeq: number;
  openWorkspaceRequestSeq: number;
};

type StoredOpenedWorkspace = {
  workOrderId: string;
  editVersionId: string;
};

export type ResetWorkOrdersOptions = {
  preserveOpenedWorkspace?: boolean;
};

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
      storage.removeItem(OPENED_WORKSPACE_STORAGE_KEY);
      return null;
    }

    return {
      workOrderId: parsed.workOrderId,
      editVersionId: parsed.editVersionId,
    };
  } catch {
    storage.removeItem(OPENED_WORKSPACE_STORAGE_KEY);
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

function createInitialWorkOrdersState(): WorkOrdersState {
  return {
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
    loadAssignedRequestSeq: 0,
    openWorkspaceRequestSeq: 0,
  };
}

export const useWorkOrdersStore = defineStore("workOrders", {
  state: createInitialWorkOrdersState,
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
    reset(options: ResetWorkOrdersOptions = {}): void {
      const nextLoadAssignedRequestSeq = this.loadAssignedRequestSeq + 1;
      const nextOpenWorkspaceRequestSeq = this.openWorkspaceRequestSeq + 1;

      Object.assign(this, {
        ...createInitialWorkOrdersState(),
        loadAssignedRequestSeq: nextLoadAssignedRequestSeq,
        openWorkspaceRequestSeq: nextOpenWorkspaceRequestSeq,
      });
      if (!options.preserveOpenedWorkspace) {
        clearStoredOpenedWorkspace();
      }
    },
    async loadAssigned() {
      const requestSeq = this.loadAssignedRequestSeq + 1;
      this.loadAssignedRequestSeq = requestSeq;
      this.isLoading = true;
      this.errorMessage = null;
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
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return;
        }

        this.items = [];
        this.errorMessage =
          "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.";
      } finally {
        if (this.loadAssignedRequestSeq === requestSeq) {
          this.isLoading = false;
        }
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
    async restoreOpenedWorkspace() {
      const storedWorkspace = readStoredOpenedWorkspace();
      if (!storedWorkspace || this.isOpeningWorkspace) {
        return;
      }

      const workOrderId = storedWorkspace.workOrderId;
      const editVersionId = storedWorkspace.editVersionId;
      if (!this.items.some((item) => item.id === workOrderId)) {
        clearStoredOpenedWorkspace();
        return;
      }

      const requestSeq = this.openWorkspaceRequestSeq + 1;
      this.openWorkspaceRequestSeq = requestSeq;
      this.isOpeningWorkspace = true;
      this.selectedWorkOrderId = workOrderId;
      this.openWorkspaceErrorByWorkOrderId = {
        ...this.openWorkspaceErrorByWorkOrderId,
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
      } catch {
        if (
          this.openWorkspaceRequestSeq === requestSeq &&
          this.selectedWorkOrderId === workOrderId
        ) {
          this.clearOpenedWorkspace();
          this.openWorkspaceErrorByWorkOrderId = {
            ...this.openWorkspaceErrorByWorkOrderId,
            [workOrderId]:
              "Не удалось восстановить рабочую версию. Обновите список или попробуйте еще раз.",
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
      clearStoredOpenedWorkspace();
    },
  },
});
