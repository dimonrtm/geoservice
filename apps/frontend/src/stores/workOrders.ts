import { defineStore } from "pinia";

import { fetchAssignedWorkOrders } from "@/api/workOrders";
import type { WorkOrderSummary } from "@/contracts/work-orders";

type WorkOrdersState = {
  items: WorkOrderSummary[];
  isLoading: boolean;
  errorMessage: string | null;
  selectedWorkOrderId: string | null;
};

export const useWorkOrdersStore = defineStore("workOrders", {
  state: (): WorkOrdersState => ({
    items: [],
    isLoading: false,
    errorMessage: null,
    selectedWorkOrderId: null,
  }),
  getters: {
    selectedWorkOrder: (state) =>
      state.items.find((item) => item.id === state.selectedWorkOrderId) ?? null,
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
    },
  },
});
