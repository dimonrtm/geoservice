import { http } from "./http";
import { parseEditVersionMap } from "@/contracts/editVersionMap";
export async function fetchEditVersionMap(
  workOrderId: string,
  editVersionId: string,
  signal?: AbortSignal,
) {
  const response = await http.get<unknown>(
    `/api/v1/work-orders/${workOrderId}/edit-versions/${editVersionId}`,
    { signal },
  );
  return parseEditVersionMap(response.data, workOrderId, editVersionId);
}
