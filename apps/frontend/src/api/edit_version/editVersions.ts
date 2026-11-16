import { http } from "../http";
import {
  parseOpenedEditVersion,
  type OpenedEditVersion,
} from "@/contracts/edit_version/open-edit-version";
import {
  parseGeometrySaveResult,
  type SaveTarget,
  type GeometrySaveRequest,
  type GeometrySaveResult,
} from "@/contracts/workspace/workspace-edit";
export async function openEditVersion(
  workOrderId: string,
): Promise<OpenedEditVersion> {
  const response = await http.post<unknown>(
    `/api/v1/work-orders/${workOrderId}/edit-versions`,
  );
  return parseOpenedEditVersion(response.data, workOrderId);
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
