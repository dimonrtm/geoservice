import { http } from "@/api/http";
import type {
  AssignedWorkOrdersResponse,
  OpenEditVersionResponse,
  WorkspaceResponse,
} from "@/contracts/work-orders";

export async function fetchAssignedWorkOrders() {
  const response = await http.get<AssignedWorkOrdersResponse>(
    "/api/v1/work-orders/assigned-to-me",
  );
  return response.data;
}

export async function openEditVersion(
  workOrderId: string,
): Promise<OpenEditVersionResponse> {
  const response = await http.post<OpenEditVersionResponse>(
    `/api/v1/work-orders/${workOrderId}/edit-versions`,
  );
  return response.data;
}

export async function fetchWorkspace(
  workOrderId: string,
  editVersionId: string,
): Promise<WorkspaceResponse> {
  const response = await http.get<WorkspaceResponse>(
    `/api/v1/work-orders/${workOrderId}/edit-versions/${editVersionId}/workspace`,
  );
  return response.data;
}
