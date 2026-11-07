import { http } from "./http";
import type { OpenEditVersionResponse } from "@/contracts/work-orders";
import {
  parseGeometrySaveResult,
  type SaveTarget,
  type GeometrySaveRequest,
  type GeometrySaveResult,
} from "@/contracts/workspace-edit";
export async function openEditVersion(
  workOrderId: string,
): Promise<OpenEditVersionResponse> {
  const response = await http.post<OpenEditVersionResponse>(
    `/api/v1/work-orders/${workOrderId}/edit-versions`,
  );
  return response.data;
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
