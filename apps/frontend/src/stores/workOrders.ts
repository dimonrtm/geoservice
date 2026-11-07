import { defineStore } from "pinia";

import { fetchAssignedWorkOrders } from "@/api/workOrders";
import { parseApiError } from "@/api/parseApiError";
import type { ErrorPresentation } from "@/contracts/api-error";
import type {
  WorkOrderStatus,
  WorkOrderSummary,
} from "@/contracts/work-orders";
import { presentWorkOrdersLoadError } from "@/errors/apiErrorPresentations";
import {
  clearStoredSelectedWorkOrder,
  storeSelectedWorkOrder,
  type ResetWorkOrdersOptions,
} from "./editorSessionStorage";
export type { ResetWorkOrdersOptions } from "./editorSessionStorage";
type WorkOrdersState = {
  items: WorkOrderSummary[];
  isLoading: boolean;
  loadError: ErrorPresentation | null;
  loadAccessDenied: boolean;
  selectedWorkOrderId: string | null;
  loadAssignedRequestSeq: number;
};

export const useWorkOrdersStore = defineStore("workOrders", {
  state: (): WorkOrdersState => ({
    items: [],
    isLoading: false,
    loadError: null,
    loadAccessDenied: false,
    selectedWorkOrderId: null,
    loadAssignedRequestSeq: 0,
  }),
  getters: {
    selectedWorkOrder: (state) =>
      state.items.find((item) => item.id === state.selectedWorkOrderId) ?? null,
  },
  actions: {
    reset(options: ResetWorkOrdersOptions = {}): void {
      const generation = this.loadAssignedRequestSeq + 1;
      this.$reset();
      this.loadAssignedRequestSeq = generation;
      if (!options.preserveSelectedWorkOrder) clearStoredSelectedWorkOrder();
    },
    async loadAssigned(): Promise<number | null> {
      const requestSeq = this.loadAssignedRequestSeq + 1;
      this.loadAssignedRequestSeq = requestSeq;
      this.isLoading = true;
      this.loadError = null;
      this.loadAccessDenied = false;
      try {
        const result = await fetchAssignedWorkOrders();
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return null;
        }

        this.items = result.workOrders;
        if (
          this.selectedWorkOrderId &&
          !this.items.some((item) => item.id === this.selectedWorkOrderId)
        )
          this.clearSelection();
      } catch (error: unknown) {
        if (this.loadAssignedRequestSeq !== requestSeq) {
          return null;
        }

        const parsed = parseApiError(error);
        this.loadError = presentWorkOrdersLoadError(parsed);
        this.loadAccessDenied =
          (parsed.kind === "http" || parsed.kind === "api") &&
          [401, 403, 404, 409].includes(parsed.status);
      } finally {
        if (this.loadAssignedRequestSeq === requestSeq) {
          this.isLoading = false;
        }
      }
      return requestSeq;
    },
    selectWorkOrder(workOrderId: string): void {
      this.selectedWorkOrderId = workOrderId;
      storeSelectedWorkOrder(workOrderId);
    },
    clearSelection(): void {
      this.selectedWorkOrderId = null;
      clearStoredSelectedWorkOrder();
    },
    updateWorkOrderStatus(workOrderId: string, status: WorkOrderStatus): void {
      this.items = this.items.map((item) =>
        item.id === workOrderId ? { ...item, status } : item,
      );
    },
  },
});
