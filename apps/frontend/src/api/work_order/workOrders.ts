import { http } from "../http";
import { parseAssignedWorkOrders } from "@/contracts/work_order/work-order-list";
export async function fetchAssignedWorkOrders() {
  const response = await http.get<unknown>(
    "/api/v1/work-orders/assigned-to-me",
  );
  return parseAssignedWorkOrders(response.data);
}
