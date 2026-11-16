import type { WorkOrderSummary } from "@/contracts/work_order/work-orders";
import type { IdentifiedWorkOrderListEntry } from "@/contracts/work_order/work-order-list";

export function workOrderListEntryFixture(
  order: WorkOrderSummary,
  rowKey = order.id,
): IdentifiedWorkOrderListEntry {
  return { ...order, rowKey, issues: [] };
}
