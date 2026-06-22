import { http } from "@/api/http";
import type { AssignedWorkOrdersResponse } from "@/contracts/work-orders";

export async function fetchAssignedWorkOrders() {
  const response = await http.get<AssignedWorkOrdersResponse>(
    "/api/v1/work-orders/assigned-to-me",
  );
  return response.data;
}
