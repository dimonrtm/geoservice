import { http } from "./http";
import { parseEditVersionChangeSet } from "@/contracts/editVersionChangeSet";
export async function fetchEditVersionChangeSet(
  workOrderId: string,
  editVersionId: string,
  signal?: AbortSignal,
) {
  const response = await http.get<unknown>(
    `/api/v1/work-orders/${workOrderId}/edit-versions/${editVersionId}/change-set`,
    { signal },
  );
  return parseEditVersionChangeSet(response.data);
}
