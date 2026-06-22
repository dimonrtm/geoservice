export type WorkOrderStatus = "assigned" | "in_progress";

export type WorkOrderSummary = {
  id: string;
  code: string;
  title: string;
  description: string | null;
  status: WorkOrderStatus;
};

export type AssignedWorkOrdersResponse = {
  workOrders: WorkOrderSummary[];
};
