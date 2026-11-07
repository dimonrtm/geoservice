import { http } from "./http";
import { parseFeatureBaseline } from "@/contracts/featureBaseline";
export async function fetchFeatureBaseline(
  workOrderId: string,
  editVersionId: string,
  featureId: string,
  signal?: AbortSignal,
) {
  const response = await http.get<unknown>(
    `/api/v1/work-orders/${workOrderId}/edit-versions/${editVersionId}/features/${featureId}/baseline`,
    { signal },
  );
  return parseFeatureBaseline(response.data, featureId);
}
