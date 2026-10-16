import { http } from "@/api/http";
import {
  parseGeometrySaveResult,
  parseWorkspaceResponse,
  type SaveTarget,
  type GeometrySaveRequest,
  type GeometrySaveResult,
} from "@/contracts/workspace-edit";
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
  return parseWorkspaceResponse(response.data, workOrderId, editVersionId);
}

export async function saveFeatureGeometry(
  target: SaveTarget,
  request: GeometrySaveRequest,
): Promise<GeometrySaveResult> {
  const response = await http.put<unknown>(
    `/api/v1/work-orders/${target.workOrderId}/edit-versions/${target.editVersionId}/features/${target.featureId}/geometry`,
    request,
  );
  return parseGeometrySaveResult(response.data, target, request.commandId);
}
